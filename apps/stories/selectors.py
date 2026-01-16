"""Selectors for stories queries."""

from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet

from .models import Chapter, Story


def story_list(*, user: AbstractUser) -> QuerySet[Story]:
    """
    Get all stories for a user.

    Args:
        user: User to filter stories by

    Returns:
        QuerySet of stories ordered by creation date (newest first)
    """
    return Story.objects.filter(user=user).order_by("-created_at")


def story_get(*, story_id: str, user: AbstractUser) -> Story | None:
    """
    Get a specific story by ID for a user.

    Args:
        story_id: Story UUID
        user: User who owns the story

    Returns:
        Story instance or None if not found
    """
    return Story.objects.filter(id=story_id, user=user).first()


def chapter_list(*, story: Story) -> QuerySet[Chapter]:
    """
    Get all chapters for a story.

    Args:
        story: Story to get chapters for

    Returns:
        QuerySet of chapters ordered by chapter number
    """
    return story.chapters.order_by("chapter_number")


def chapter_get_latest(*, story: Story) -> Chapter | None:
    """
    Get the latest chapter of a story.

    Args:
        story: Story to get latest chapter for

    Returns:
        Latest Chapter instance or None if no chapters exist
    """
    return story.chapters.order_by("-chapter_number").first()
