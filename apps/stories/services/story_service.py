"""Story service for business logic."""

from django.contrib.auth.models import AbstractUser

from apps.stories.models import Chapter, Story, StoryStatus


def story_create(
    *,
    user: AbstractUser,
    title: str,
    premise: str,
    language: str = "ru",
    max_chapters: int = 10,
) -> Story:
    """
    Create a new story.

    Args:
        user: User who owns the story
        title: Story title
        premise: Initial story setup
        language: Language code (ru or en)
        max_chapters: Maximum number of chapters

    Returns:
        Created Story instance
    """
    story = Story(
        user=user,
        title=title,
        premise=premise,
        language=language,
        max_chapters=max_chapters,
    )
    story.full_clean()
    story.save()
    return story


def story_complete(*, story: Story) -> Story:
    """
    Mark story as completed.

    Args:
        story: Story to complete

    Returns:
        Updated Story instance
    """
    story.status = StoryStatus.COMPLETED
    story.save(update_fields=["status", "updated_at"])
    return story


def story_cancel(*, story: Story) -> Story:
    """
    Cancel a story.

    Args:
        story: Story to cancel

    Returns:
        Updated Story instance
    """
    story.status = StoryStatus.CANCELLED
    story.save(update_fields=["status", "updated_at"])
    return story


def chapter_create(
    *,
    story: Story,
    chapter_number: int,
    content: str = "",
    choices: list[str] | None = None,
) -> Chapter:
    """
    Create a new chapter.

    Args:
        story: Parent story
        chapter_number: Chapter number (1-indexed)
        content: Chapter text content
        choices: List of continuation options

    Returns:
        Created Chapter instance
    """
    chapter = Chapter(
        story=story,
        chapter_number=chapter_number,
        content=content,
        choices=choices or [],
    )
    chapter.full_clean()
    chapter.save()
    return chapter


def chapter_select_choice(*, chapter: Chapter, choice: str) -> Chapter:
    """
    Select a choice for continuation.

    Args:
        chapter: Chapter to update
        choice: Selected choice text

    Returns:
        Updated Chapter instance
    """
    chapter.selected_choice = choice
    chapter.save(update_fields=["selected_choice"])
    return chapter


def chapter_mark_generated(*, chapter: Chapter) -> Chapter:
    """
    Mark chapter as generated.

    Args:
        chapter: Chapter to update

    Returns:
        Updated Chapter instance
    """
    chapter.is_generated = True
    chapter.save(update_fields=["is_generated"])
    return chapter
