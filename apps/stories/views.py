"""Views for the stories app."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import Story


class HomeView(ListView):
    """Home page with story creation form and user's stories list."""

    model = Story
    template_name = "stories/home.html"
    context_object_name = "stories"

    def get_queryset(self):
        """Return stories for authenticated user only."""
        if self.request.user.is_authenticated:
            return Story.objects.filter(user=self.request.user)
        return Story.objects.none()


class StoryDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a single story with its chapters."""

    model = Story
    template_name = "stories/story_detail.html"
    context_object_name = "story"
    pk_url_kwarg = "story_id"

    def get_object(self, queryset=None):
        """Get story and verify ownership."""
        story = get_object_or_404(Story, pk=self.kwargs["story_id"])
        if story.user != self.request.user:
            raise Http404("Story not found")
        return story

    def get_context_data(self, **kwargs):
        """Add chapters to context."""
        context = super().get_context_data(**kwargs)
        context["chapters"] = self.object.chapters.all()
        return context
