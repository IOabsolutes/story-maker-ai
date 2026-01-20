from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from common.celery_utils import safe_delay
from common.types import AuthenticatedHttpRequest

from .models import Chapter, Story, StoryStatus, TaskStatus, TaskStatusChoice
from .services.story_service import chapter_select_choice, story_create
from .tasks import generate_chapter


class HomeView(ListView):
    model = Story
    template_name = "stories/home.html"
    context_object_name = "stories"

    def get_queryset(self) -> QuerySet[Story]:
        if self.request.user.is_authenticated:
            return Story.objects.filter(user=self.request.user).order_by("-created_at")
        return Story.objects.none()

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse | HttpResponseRedirect:
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        title = request.POST.get("title", "").strip()
        premise = request.POST.get("premise", "").strip()
        language = request.POST.get("language", "ru")
        max_chapters_str = request.POST.get("max_chapters", "10")

        errors: list[str] = []
        if len(title) < 10:
            errors.append("Story title must be at least 10 characters.")
        if len(premise) < 20:
            errors.append("Story premise must be at least 20 characters.")

        try:
            max_chapters = int(max_chapters_str)
            if not (3 <= max_chapters <= 20):
                errors.append("Max chapters must be between 3 and 20.")
        except ValueError:
            errors.append("Invalid max chapters value.")
            max_chapters = 10

        if errors:
            for error in errors:
                messages.error(request, error)
            return self.get(request, *args, **kwargs)

        # Create story
        story = story_create(
            user=request.user,
            title=title,
            premise=premise,
            language=language,
            max_chapters=max_chapters,
        )

        # Start generation with broker error handling
        result = safe_delay(
            generate_chapter,
            story_id=str(story.id),
            chapter_number=1,
        )

        if result.success:
            TaskStatus.objects.create(
                id=result.task_id,
                story=story,
                chapter_number=1,
            )
            messages.success(
                request, f'Story "{title}" created! Generating first chapter...'
            )
        else:
            messages.warning(
                request,
                f'Story "{title}" created, but generation service is temporarily '
                "unavailable. Please refresh the page to retry.",
            )

        return redirect("stories:story_detail", story_id=story.id)


class StoryDetailView(LoginRequiredMixin, DetailView):
    model = Story
    template_name = "stories/story_detail.html"
    context_object_name = "story"
    pk_url_kwarg = "story_id"

    def get_object(self, queryset: QuerySet[Story] | None = None) -> Story:
        story = get_object_or_404(
            Story.objects.prefetch_related("chapters", "task_statuses"),
            pk=self.kwargs["story_id"],
        )
        if story.user != self.request.user:
            raise Http404("Story not found")
        return story

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["chapters"] = self.object.chapters.order_by("chapter_number")

        # Check if there's an active generation task
        active_task = self.object.task_statuses.filter(
            status__in=[TaskStatusChoice.PENDING, TaskStatusChoice.PROCESSING]
        ).first()

        context["is_generating"] = active_task is not None
        context["task_id"] = str(active_task.id) if active_task else None

        # Last chapter for choice form
        last_chapter = self.object.chapters.order_by("-chapter_number").first()
        context["last_chapter"] = last_chapter

        return context


class StoryDeleteView(LoginRequiredMixin, View):
    def post(
        self, request: AuthenticatedHttpRequest, story_id: str
    ) -> HttpResponseRedirect:
        story = get_object_or_404(Story, pk=story_id)
        if story.user != request.user:
            raise Http404("Story not found")

        title = story.title
        story.delete()
        messages.success(request, f'Story "{title}" has been deleted.')
        return redirect("stories:home")


class StoryRestartView(LoginRequiredMixin, View):
    def post(
        self, request: AuthenticatedHttpRequest, story_id: str
    ) -> HttpResponseRedirect:
        story = get_object_or_404(Story, pk=story_id)
        if story.user != request.user:
            raise Http404("Story not found")

        # Check for active generation task (race condition protection)
        active_task = story.task_statuses.filter(
            status__in=[TaskStatusChoice.PENDING, TaskStatusChoice.PROCESSING]
        ).exists()
        if active_task:
            messages.warning(request, "A chapter is already being generated. Please wait.")
            return redirect("stories:story_detail", story_id=story.id)

        with transaction.atomic():
            # Delete all chapters
            story.chapters.all().delete()

            # Delete old task statuses
            story.task_statuses.all().delete()

            # Reset status
            story.status = StoryStatus.IN_PROGRESS
            story.save(update_fields=["status", "updated_at"])

        # Queue task AFTER transaction commits to avoid race condition
        # See: https://testdriven.io/blog/celery-database-transactions/
        story_id_str = str(story.id)

        result = safe_delay(
            generate_chapter,
            story_id=story_id_str,
            chapter_number=1,
        )

        if result.success:
            TaskStatus.objects.create(
                id=result.task_id,
                story_id=story_id_str,
                chapter_number=1,
            )
            messages.success(
                request, "Story has been restarted. Generating first chapter..."
            )
        else:
            messages.warning(
                request,
                "Story has been reset, but generation service is temporarily "
                "unavailable. Please refresh the page to retry.",
            )

        return redirect("stories:story_detail", story_id=story.id)


class ChapterChooseView(LoginRequiredMixin, View):
    def post(
        self, request: AuthenticatedHttpRequest, chapter_id: str
    ) -> HttpResponseRedirect:
        chapter = get_object_or_404(
            Chapter.objects.select_related("story"),
            pk=chapter_id,
        )
        story = chapter.story

        if story.user != request.user:
            raise Http404("Chapter not found")

        if not story.can_continue:
            messages.error(request, "This story has already been completed.")
            return redirect("stories:story_detail", story_id=story.id)

        # Check for active generation task (race condition protection)
        active_task = story.task_statuses.filter(
            status__in=[TaskStatusChoice.PENDING, TaskStatusChoice.PROCESSING]
        ).exists()
        if active_task:
            messages.warning(request, "A chapter is already being generated. Please wait.")
            return redirect("stories:story_detail", story_id=story.id)

        # Get choice from form
        selected_choice = request.POST.get("selected_choice", "").strip()
        user_input = request.POST.get("user_input", "").strip()

        # Server-side validation for user_input
        if user_input and len(user_input) > 500:
            messages.error(request, "Custom continuation must be 500 characters or less.")
            return redirect("stories:story_detail", story_id=story.id)

        choice = user_input if user_input else selected_choice

        if not choice:
            messages.error(
                request, "Please select a choice or enter your own continuation."
            )
            return redirect("stories:story_detail", story_id=story.id)

        # Save choice
        chapter_select_choice(chapter=chapter, choice=choice)

        # Start generation of next chapter with broker error handling
        next_chapter_number = chapter.chapter_number + 1
        result = safe_delay(
            generate_chapter,
            story_id=str(story.id),
            chapter_number=next_chapter_number,
            selected_choice=choice,
        )

        if result.success:
            TaskStatus.objects.create(
                id=result.task_id,
                story=story,
                chapter_number=next_chapter_number,
            )
            messages.success(request, f"Generating chapter {next_chapter_number}...")
        else:
            messages.warning(
                request,
                "Choice saved, but generation service is temporarily unavailable. "
                "Please refresh the page to retry.",
            )

        return redirect("stories:story_detail", story_id=story.id)
