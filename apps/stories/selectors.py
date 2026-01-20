from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet

from .models import Chapter, Story


def story_list(*, user: AbstractUser) -> QuerySet[Story]:
    return Story.objects.filter(user=user).order_by("-created_at")


def story_get(*, story_id: str, user: AbstractUser) -> Story | None:
    return Story.objects.filter(id=story_id, user=user).first()


def chapter_list(*, story: Story) -> QuerySet[Chapter]:
    return story.chapters.order_by("chapter_number")


def chapter_get_latest(*, story: Story) -> Chapter | None:
    return story.chapters.order_by("-chapter_number").first()
