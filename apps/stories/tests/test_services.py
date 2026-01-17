"""Tests for stories app services."""

import pytest
from django.core.exceptions import ValidationError

from apps.stories.models import Chapter, Story, StoryStatus
from apps.stories.services.story_service import (
    chapter_create,
    chapter_mark_generated,
    chapter_select_choice,
    story_cancel,
    story_complete,
    story_create,
)
from apps.stories.tests.factories import ChapterFactory, StoryFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestStoryCreate:
    """Tests for story_create service function."""

    def test_story_create_with_required_fields(self, user):
        """story_create creates a story with required fields."""
        story = story_create(
            user=user,
            title="Test Story",
            premise="A test story premise",
        )
        assert story.id is not None
        assert story.user == user
        assert story.title == "Test Story"
        assert story.premise == "A test story premise"

    def test_story_create_with_default_language(self, user):
        """story_create uses Russian as default language."""
        story = story_create(
            user=user,
            title="Test Story",
            premise="A test story premise",
        )
        assert story.language == "ru"

    def test_story_create_with_custom_language(self, user):
        """story_create accepts custom language."""
        story = story_create(
            user=user,
            title="Test Story",
            premise="A test story premise",
            language="en",
        )
        assert story.language == "en"

    def test_story_create_with_default_max_chapters(self, user):
        """story_create uses 10 as default max_chapters."""
        story = story_create(
            user=user,
            title="Test Story",
            premise="A test story premise",
        )
        assert story.max_chapters == 10

    def test_story_create_with_custom_max_chapters(self, user):
        """story_create accepts custom max_chapters."""
        story = story_create(
            user=user,
            title="Test Story",
            premise="A test story premise",
            max_chapters=5,
        )
        assert story.max_chapters == 5

    def test_story_create_sets_in_progress_status(self, user):
        """story_create sets IN_PROGRESS status."""
        story = story_create(
            user=user,
            title="Test Story",
            premise="A test story premise",
        )
        assert story.status == StoryStatus.IN_PROGRESS

    def test_story_create_validates_data(self, user):
        """story_create runs full_clean validation."""
        with pytest.raises(ValidationError):
            story_create(
                user=user,
                title="",  # Empty title should fail validation
                premise="A test story premise",
            )


class TestStoryComplete:
    """Tests for story_complete service function."""

    def test_story_complete_changes_status(self):
        """story_complete changes status to COMPLETED."""
        story = StoryFactory(status=StoryStatus.IN_PROGRESS)
        result = story_complete(story=story)
        assert result.status == StoryStatus.COMPLETED

    def test_story_complete_updates_database(self):
        """story_complete persists changes to database."""
        story = StoryFactory(status=StoryStatus.IN_PROGRESS)
        story_complete(story=story)
        story.refresh_from_db()
        assert story.status == StoryStatus.COMPLETED

    def test_story_complete_returns_story(self):
        """story_complete returns the updated story."""
        story = StoryFactory(status=StoryStatus.IN_PROGRESS)
        result = story_complete(story=story)
        assert result == story


class TestStoryCancel:
    """Tests for story_cancel service function."""

    def test_story_cancel_changes_status(self):
        """story_cancel changes status to CANCELLED."""
        story = StoryFactory(status=StoryStatus.IN_PROGRESS)
        result = story_cancel(story=story)
        assert result.status == StoryStatus.CANCELLED

    def test_story_cancel_updates_database(self):
        """story_cancel persists changes to database."""
        story = StoryFactory(status=StoryStatus.IN_PROGRESS)
        story_cancel(story=story)
        story.refresh_from_db()
        assert story.status == StoryStatus.CANCELLED

    def test_story_cancel_returns_story(self):
        """story_cancel returns the updated story."""
        story = StoryFactory(status=StoryStatus.IN_PROGRESS)
        result = story_cancel(story=story)
        assert result == story


class TestChapterCreate:
    """Tests for chapter_create service function."""

    def test_chapter_create_with_required_fields(self):
        """chapter_create creates a chapter with required fields."""
        story = StoryFactory()
        chapter = chapter_create(
            story=story,
            chapter_number=1,
        )
        assert chapter.id is not None
        assert chapter.story == story
        assert chapter.chapter_number == 1

    def test_chapter_create_with_empty_content(self):
        """chapter_create defaults to empty content."""
        story = StoryFactory()
        chapter = chapter_create(
            story=story,
            chapter_number=1,
        )
        assert chapter.content == ""

    def test_chapter_create_with_custom_content(self):
        """chapter_create accepts custom content."""
        story = StoryFactory()
        chapter = chapter_create(
            story=story,
            chapter_number=1,
            content="Once upon a time...",
        )
        assert chapter.content == "Once upon a time..."

    def test_chapter_create_with_empty_choices(self):
        """chapter_create handles None choices as empty list."""
        story = StoryFactory()
        chapter = chapter_create(
            story=story,
            chapter_number=1,
            choices=None,
        )
        assert chapter.choices == []

    def test_chapter_create_with_custom_choices(self):
        """chapter_create accepts custom choices."""
        story = StoryFactory()
        choices = ["Go left", "Go right", "Stay"]
        chapter = chapter_create(
            story=story,
            chapter_number=1,
            choices=choices,
        )
        assert chapter.choices == choices

    def test_chapter_create_not_generated_by_default(self):
        """chapter_create sets is_generated to False."""
        story = StoryFactory()
        chapter = chapter_create(
            story=story,
            chapter_number=1,
        )
        assert chapter.is_generated is False

    def test_chapter_create_returns_chapter(self):
        """chapter_create returns the created chapter."""
        story = StoryFactory()
        chapter = chapter_create(
            story=story,
            chapter_number=1,
        )
        assert isinstance(chapter, Chapter)


class TestChapterSelectChoice:
    """Tests for chapter_select_choice service function."""

    def test_chapter_select_choice_sets_choice(self):
        """chapter_select_choice sets selected_choice."""
        chapter = ChapterFactory(selected_choice=None)
        result = chapter_select_choice(chapter=chapter, choice="Go left")
        assert result.selected_choice == "Go left"

    def test_chapter_select_choice_updates_database(self):
        """chapter_select_choice persists changes to database."""
        chapter = ChapterFactory(selected_choice=None)
        chapter_select_choice(chapter=chapter, choice="Go right")
        chapter.refresh_from_db()
        assert chapter.selected_choice == "Go right"

    def test_chapter_select_choice_returns_chapter(self):
        """chapter_select_choice returns the updated chapter."""
        chapter = ChapterFactory(selected_choice=None)
        result = chapter_select_choice(chapter=chapter, choice="Stay")
        assert result == chapter

    def test_chapter_select_choice_accepts_custom_input(self):
        """chapter_select_choice accepts custom user input."""
        chapter = ChapterFactory(selected_choice=None)
        custom_input = "I want to explore the mysterious cave"
        result = chapter_select_choice(chapter=chapter, choice=custom_input)
        assert result.selected_choice == custom_input


class TestChapterMarkGenerated:
    """Tests for chapter_mark_generated service function."""

    def test_chapter_mark_generated_sets_flag(self):
        """chapter_mark_generated sets is_generated to True."""
        chapter = ChapterFactory(is_generated=False)
        result = chapter_mark_generated(chapter=chapter)
        assert result.is_generated is True

    def test_chapter_mark_generated_updates_database(self):
        """chapter_mark_generated persists changes to database."""
        chapter = ChapterFactory(is_generated=False)
        chapter_mark_generated(chapter=chapter)
        chapter.refresh_from_db()
        assert chapter.is_generated is True

    def test_chapter_mark_generated_returns_chapter(self):
        """chapter_mark_generated returns the updated chapter."""
        chapter = ChapterFactory(is_generated=False)
        result = chapter_mark_generated(chapter=chapter)
        assert result == chapter
