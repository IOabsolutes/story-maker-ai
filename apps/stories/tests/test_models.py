"""Tests for stories app models."""

import pytest
from django.db import IntegrityError

from apps.stories.models import (
    Chapter,
    Story,
    StoryStatus,
    TaskStatus,
    TaskStatusChoice,
)
from apps.stories.tests.factories import (
    ChapterFactory,
    StoryFactory,
    TaskStatusFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


class TestStoryModel:
    """Tests for Story model."""

    def test_story_create(self):
        """Story can be created with valid data."""
        story = StoryFactory()
        assert story.id is not None
        assert story.pk is not None

    def test_story_str(self):
        """String representation returns 'title (username)'."""
        user = UserFactory(username="john")
        story = StoryFactory(user=user, title="My Adventure")
        assert str(story) == "My Adventure (john)"

    def test_story_default_status(self):
        """New stories have IN_PROGRESS status by default."""
        story = StoryFactory()
        assert story.status == StoryStatus.IN_PROGRESS

    def test_story_default_language(self):
        """Stories default to Russian language."""
        story = StoryFactory()
        assert story.language == "ru"

    def test_chapter_count_zero(self):
        """chapter_count returns 0 when no chapters exist."""
        story = StoryFactory()
        assert story.chapter_count == 0

    def test_chapter_count_with_generated(self):
        """chapter_count only counts is_generated=True chapters."""
        story = StoryFactory()
        ChapterFactory(story=story, chapter_number=1, is_generated=True)
        ChapterFactory(story=story, chapter_number=2, is_generated=True)
        ChapterFactory(story=story, chapter_number=3, is_generated=False)
        assert story.chapter_count == 2

    def test_is_complete_false(self):
        """is_complete returns False for IN_PROGRESS story."""
        story = StoryFactory(status=StoryStatus.IN_PROGRESS)
        assert story.is_complete is False

    def test_is_complete_true(self):
        """is_complete returns True for COMPLETED story."""
        story = StoryFactory(status=StoryStatus.COMPLETED)
        assert story.is_complete is True

    def test_can_continue_true(self):
        """can_continue returns True when in progress and under chapter limit."""
        story = StoryFactory(status=StoryStatus.IN_PROGRESS, max_chapters=10)
        ChapterFactory(story=story, chapter_number=1, is_generated=True)
        assert story.can_continue is True

    def test_can_continue_false_completed(self):
        """can_continue returns False when story is completed."""
        story = StoryFactory(status=StoryStatus.COMPLETED, max_chapters=10)
        assert story.can_continue is False

    def test_can_continue_false_cancelled(self):
        """can_continue returns False when story is cancelled."""
        story = StoryFactory(status=StoryStatus.CANCELLED, max_chapters=10)
        assert story.can_continue is False

    def test_can_continue_false_max_reached(self):
        """can_continue returns False when max chapters reached."""
        story = StoryFactory(status=StoryStatus.IN_PROGRESS, max_chapters=2)
        ChapterFactory(story=story, chapter_number=1, is_generated=True)
        ChapterFactory(story=story, chapter_number=2, is_generated=True)
        assert story.can_continue is False

    def test_story_ordering(self):
        """Stories are ordered by -created_at (newest first)."""
        story1 = StoryFactory()
        story2 = StoryFactory()
        stories = list(Story.objects.all())
        assert stories[0] == story2
        assert stories[1] == story1


class TestChapterModel:
    """Tests for Chapter model."""

    def test_chapter_create(self):
        """Chapter can be created with valid data."""
        chapter = ChapterFactory()
        assert chapter.id is not None
        assert chapter.pk is not None

    def test_chapter_str(self):
        """String representation returns 'Chapter N of title'."""
        story = StoryFactory(title="Epic Quest")
        chapter = ChapterFactory(story=story, chapter_number=3)
        assert str(chapter) == "Chapter 3 of Epic Quest"

    def test_chapter_default_not_generated(self):
        """New chapters have is_generated=False by default in model."""
        story = StoryFactory()
        chapter = Chapter.objects.create(story=story, chapter_number=1)
        assert chapter.is_generated is False

    def test_chapter_unique_constraint(self):
        """Cannot create two chapters with same number in same story."""
        story = StoryFactory()
        ChapterFactory(story=story, chapter_number=1)
        with pytest.raises(IntegrityError):
            ChapterFactory(story=story, chapter_number=1)

    def test_chapter_same_number_different_stories(self):
        """Same chapter number can exist in different stories."""
        story1 = StoryFactory()
        story2 = StoryFactory()
        chapter1 = ChapterFactory(story=story1, chapter_number=1)
        chapter2 = ChapterFactory(story=story2, chapter_number=1)
        assert chapter1.chapter_number == chapter2.chapter_number

    def test_is_final_true(self):
        """is_final returns True when chapter_number >= max_chapters."""
        story = StoryFactory(max_chapters=3)
        chapter = ChapterFactory(story=story, chapter_number=3)
        assert chapter.is_final is True

    def test_is_final_false(self):
        """is_final returns False when chapter_number < max_chapters."""
        story = StoryFactory(max_chapters=5)
        chapter = ChapterFactory(story=story, chapter_number=2)
        assert chapter.is_final is False

    def test_can_select_choice_true(self):
        """can_select_choice returns True when generated, not selected, not final."""
        story = StoryFactory(max_chapters=5)
        chapter = ChapterFactory(
            story=story,
            chapter_number=1,
            is_generated=True,
            selected_choice=None,
        )
        assert chapter.can_select_choice is True

    def test_can_select_choice_false_not_generated(self):
        """can_select_choice returns False when not generated."""
        story = StoryFactory(max_chapters=5)
        chapter = ChapterFactory(
            story=story,
            chapter_number=1,
            is_generated=False,
            selected_choice=None,
        )
        assert chapter.can_select_choice is False

    def test_can_select_choice_false_already_selected(self):
        """can_select_choice returns False when choice already selected."""
        story = StoryFactory(max_chapters=5)
        chapter = ChapterFactory(
            story=story,
            chapter_number=1,
            is_generated=True,
            selected_choice="Go left",
        )
        assert chapter.can_select_choice is False

    def test_can_select_choice_false_final(self):
        """can_select_choice returns False for final chapter."""
        story = StoryFactory(max_chapters=3)
        chapter = ChapterFactory(
            story=story,
            chapter_number=3,
            is_generated=True,
            selected_choice=None,
        )
        assert chapter.can_select_choice is False

    def test_choices_json_field(self):
        """choices JSONField correctly stores and retrieves list."""
        choices_list = ["Option A", "Option B", "Option C"]
        chapter = ChapterFactory(choices=choices_list)
        chapter.refresh_from_db()
        assert chapter.choices == choices_list

    def test_chapter_ordering(self):
        """Chapters are ordered by chapter_number ascending."""
        story = StoryFactory()
        ChapterFactory(story=story, chapter_number=3)
        ChapterFactory(story=story, chapter_number=1)
        ChapterFactory(story=story, chapter_number=2)
        chapters = list(story.chapters.all())
        assert [c.chapter_number for c in chapters] == [1, 2, 3]


class TestTaskStatusModel:
    """Tests for TaskStatus model."""

    def test_task_status_create(self):
        """TaskStatus can be created with valid data."""
        task_status = TaskStatusFactory()
        assert task_status.id is not None
        assert task_status.pk is not None

    def test_task_status_str(self):
        """String representation returns 'Task {id} - {status}'."""
        task_status = TaskStatusFactory(status=TaskStatusChoice.PROCESSING)
        assert f"Task {task_status.id} - processing" == str(task_status)

    def test_task_status_default_pending(self):
        """New task statuses have PENDING status by default."""
        task_status = TaskStatusFactory()
        assert task_status.status == TaskStatusChoice.PENDING

    def test_mark_processing(self):
        """mark_processing changes status to PROCESSING."""
        task_status = TaskStatusFactory(status=TaskStatusChoice.PENDING)
        task_status.mark_processing()
        task_status.refresh_from_db()
        assert task_status.status == TaskStatusChoice.PROCESSING

    def test_mark_completed(self):
        """mark_completed changes status to COMPLETED."""
        task_status = TaskStatusFactory(status=TaskStatusChoice.PROCESSING)
        task_status.mark_completed()
        task_status.refresh_from_db()
        assert task_status.status == TaskStatusChoice.COMPLETED

    def test_mark_failed(self):
        """mark_failed changes status to FAILED and sets error message."""
        task_status = TaskStatusFactory(status=TaskStatusChoice.PROCESSING)
        error_msg = "Connection timeout"
        task_status.mark_failed(error_msg)
        task_status.refresh_from_db()
        assert task_status.status == TaskStatusChoice.FAILED
        assert task_status.error_message == error_msg

    def test_task_status_ordering(self):
        """Task statuses are ordered by -created_at (newest first)."""
        story = StoryFactory()
        ts1 = TaskStatusFactory(story=story, chapter_number=1)
        ts2 = TaskStatusFactory(story=story, chapter_number=2)
        statuses = list(TaskStatus.objects.filter(story=story))
        assert statuses[0] == ts2
        assert statuses[1] == ts1
