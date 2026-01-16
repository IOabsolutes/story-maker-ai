"""Celery tasks for the stories app."""

import logging
import uuid
from typing import Any

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from apps.stories.models import Chapter, Story, TaskStatus
from apps.stories.selectors import chapter_list
from apps.stories.services import PromptBuilder, ollama_client
from apps.stories.services.story_service import story_complete
from common.exceptions import StoryGenerationError

logger = logging.getLogger(__name__)


@shared_task(  # type: ignore[untyped-decorator]
    bind=True,
    autoretry_for=(StoryGenerationError,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
    acks_late=True,
    reject_on_worker_lost=True,
    track_started=True,
)
def generate_chapter(
    self: Any,
    story_id: str,
    chapter_number: int,
    selected_choice: str | None = None,
) -> dict[str, str | int]:
    """
    Generate a new chapter for a story using Ollama LLM.

    Args:
        story_id: UUID of the story
        chapter_number: Number of the chapter to generate (1-based)
        selected_choice: User's selected continuation from previous chapter

    Returns:
        dict with chapter_id, story_id, chapter_number and status

    Raises:
        StoryGenerationError: Triggers automatic retry with exponential backoff
    """
    task_id = uuid.UUID(self.request.id) if self.request.id else uuid.uuid4()
    task_status: TaskStatus | None = None

    logger.info(
        f"Generating chapter {chapter_number} for story {story_id} "
        f"(task_id: {task_id}, attempt: {self.request.retries + 1})"
    )

    try:
        # 1. Get Story
        story = Story.objects.get(id=story_id)

        # 2. Create/update TaskStatus
        task_status, _ = TaskStatus.objects.get_or_create(
            id=task_id,
            defaults={"story": story, "chapter_number": chapter_number},
        )
        task_status.mark_processing()

        # 3. Get previous chapters
        previous_chapters = list(chapter_list(story=story))

        # 4. Create Chapter placeholder or get existing
        chapter, created = Chapter.objects.get_or_create(
            story=story,
            chapter_number=chapter_number,
            defaults={"content": "", "choices": [], "is_generated": False},
        )

        if created:
            logger.debug(f"Created new chapter {chapter_number} for story {story_id}")
        else:
            logger.debug(f"Using existing chapter {chapter_number} for story {story_id}")

        # 5. Build prompt
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_chapter_prompt(
            story=story,
            previous_chapters=previous_chapters,
            selected_choice=selected_choice,
            chapter_number=chapter_number,
        )

        # 6. Call Ollama
        logger.info(f"Calling Ollama for chapter {chapter_number}")
        response = ollama_client.generate_sync(prompt)

        # 7. Parse response
        parsed = prompt_builder.parse_response(response.text)

        # 8. Update Chapter
        chapter.content = parsed["content"]
        chapter.choices = parsed["choices"]
        chapter.is_generated = True
        chapter.save(update_fields=["content", "choices", "is_generated"])

        logger.info(
            f"Chapter {chapter_number} generated successfully "
            f"(content: {len(parsed['content'])} chars, choices: {len(parsed['choices'])})"
        )

        # 9. Update TaskStatus
        task_status.mark_completed()

        # 10. Check if final chapter -> complete story
        if chapter_number >= story.max_chapters:
            story_complete(story=story)
            logger.info(f"Story {story_id} completed (final chapter {chapter_number})")

        return {
            "status": "success",
            "story_id": str(story_id),
            "chapter_id": str(chapter.id),
            "chapter_number": chapter_number,
        }

    except Story.DoesNotExist:
        logger.error(f"Story {story_id} not found")
        return {"status": "error", "error": "Story not found", "story_id": story_id}

    except SoftTimeLimitExceeded:
        logger.error(f"Timeout generating chapter {chapter_number} for story {story_id}")
        if task_status:
            task_status.mark_failed("Generation timed out")
        raise

    except StoryGenerationError as e:
        logger.warning(
            f"Generation error for chapter {chapter_number} "
            f"(attempt {self.request.retries + 1}/{self.max_retries + 1}): {e}"
        )
        # Mark failed only on final retry
        if self.request.retries >= self.max_retries:
            if task_status:
                task_status.mark_failed(str(e))
            logger.error(
                f"All retries exhausted for chapter {chapter_number}, story {story_id}"
            )
        raise
