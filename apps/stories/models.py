"""Data models for the stories app."""

import uuid

from django.contrib.auth.models import User
from django.db import models


class StoryStatus(models.TextChoices):
    """Status choices for a Story."""

    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class LanguageChoice(models.TextChoices):
    """Language choices for story generation."""

    RUSSIAN = "ru", "Russian"
    ENGLISH = "en", "English"


class Story(models.Model):
    """
    Represents an interactive story created by a user.

    Business Rules:
    - Each story belongs to exactly one user
    - Stories start with status 'in_progress'
    - max_chapters limits how many chapters can be generated (1-20)
    - Deleting a story cascades to all related chapters and task statuses
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stories")
    title = models.CharField(max_length=255)
    premise = models.TextField(help_text="Initial story setup: characters, setting, theme")
    language = models.CharField(
        max_length=2,
        choices=LanguageChoice.choices,
        default=LanguageChoice.RUSSIAN,
    )
    max_chapters = models.PositiveIntegerField(default=10)
    status = models.CharField(
        max_length=20,
        choices=StoryStatus.choices,
        default=StoryStatus.IN_PROGRESS,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "stories"

    def __str__(self) -> str:
        return f"{self.title} ({self.user.username})"

    @property
    def chapter_count(self) -> int:
        """Returns number of generated chapters."""
        return self.chapters.filter(is_generated=True).count()

    @property
    def is_complete(self) -> bool:
        """Story is complete when max chapters reached or manually completed."""
        return self.status == StoryStatus.COMPLETED

    @property
    def can_continue(self) -> bool:
        """Story can continue if in progress and under chapter limit."""
        return self.status == StoryStatus.IN_PROGRESS and self.chapter_count < self.max_chapters


class Chapter(models.Model):
    """
    Represents a single chapter in a story.

    Business Rules:
    - Chapters are numbered sequentially starting from 1
    - Each chapter has 2-3 choices for continuing (except final chapter)
    - selected_choice is null until user picks a continuation
    - is_generated is False while Celery task is processing
    - Only one chapter per story can have is_generated=False at a time
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="chapters")
    chapter_number = models.PositiveIntegerField()
    content = models.TextField(blank=True)
    choices = models.JSONField(default=list, help_text="List of 2-3 continuation options")
    selected_choice = models.TextField(
        null=True,
        blank=True,
        help_text="User's selected continuation or custom input",
    )
    is_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chapter_number"]
        unique_together = ["story", "chapter_number"]

    def __str__(self) -> str:
        return f"Chapter {self.chapter_number} of {self.story.title}"

    @property
    def is_final(self) -> bool:
        """True if this is the last possible chapter."""
        return self.chapter_number >= self.story.max_chapters

    @property
    def can_select_choice(self) -> bool:
        """User can select choice if generated and not already selected."""
        return self.is_generated and self.selected_choice is None and not self.is_final


class TaskStatusChoice(models.TextChoices):
    """Status choices for a TaskStatus."""

    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class TaskStatus(models.Model):
    """
    Tracks Celery task status for chapter generation.

    Business Rules:
    - id matches Celery task_id for correlation
    - Allows resumption after system restart
    - Only one pending/processing task per story at a time
    - Failed tasks store error message for debugging
    """

    id = models.UUIDField(primary_key=True, help_text="Matches Celery task_id")
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="task_statuses")
    chapter_number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=TaskStatusChoice.choices,
        default=TaskStatusChoice.PENDING,
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "task statuses"

    def __str__(self) -> str:
        return f"Task {self.id} - {self.status}"

    def mark_processing(self) -> None:
        """Transition to processing state."""
        self.status = TaskStatusChoice.PROCESSING
        self.save(update_fields=["status", "updated_at"])

    def mark_completed(self) -> None:
        """Transition to completed state."""
        self.status = TaskStatusChoice.COMPLETED
        self.save(update_fields=["status", "updated_at"])

    def mark_failed(self, error: str) -> None:
        """Transition to failed state with error message."""
        self.status = TaskStatusChoice.FAILED
        self.error_message = error
        self.save(update_fields=["status", "error_message", "updated_at"])
