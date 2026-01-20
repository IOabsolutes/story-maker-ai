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
    story.status = StoryStatus.COMPLETED
    story.save(update_fields=["status", "updated_at"])
    return story


def story_cancel(*, story: Story) -> Story:
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
    chapter.selected_choice = choice
    chapter.save(update_fields=["selected_choice"])
    return chapter


def chapter_mark_generated(*, chapter: Chapter) -> Chapter:
    chapter.is_generated = True
    chapter.save(update_fields=["is_generated"])
    return chapter
