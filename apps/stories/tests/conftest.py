"""Pytest fixtures for stories app tests."""

import pytest

from apps.stories.tests.factories import (
    ChapterFactory,
    StoryFactory,
    TaskStatusFactory,
)


@pytest.fixture
def story(user):
    """Create a test story owned by the user fixture."""
    return StoryFactory(user=user)


@pytest.fixture
def story_with_chapters(user):
    """Create a story with 3 generated chapters."""
    story = StoryFactory(user=user, max_chapters=5)
    ChapterFactory(story=story, chapter_number=1)
    ChapterFactory(story=story, chapter_number=2)
    ChapterFactory(story=story, chapter_number=3, selected_choice=None)
    return story


@pytest.fixture
def chapter(story):
    """Create a test chapter for the story fixture."""
    return ChapterFactory(story=story, chapter_number=1)


@pytest.fixture
def pending_chapter(story):
    """Create a chapter that is not yet generated (pending)."""
    return ChapterFactory(
        story=story,
        chapter_number=1,
        content="",
        choices=[],
        is_generated=False,
    )


@pytest.fixture
def final_chapter(user):
    """Create a final chapter (chapter_number == max_chapters)."""
    story = StoryFactory(user=user, max_chapters=3)
    return ChapterFactory(
        story=story,
        chapter_number=3,
        choices=[],  # Final chapters have no choices
    )


@pytest.fixture
def task_status(story):
    """Create a test task status for the story fixture."""
    return TaskStatusFactory(story=story, chapter_number=1)
