"""Celery tasks for the stories app."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_chapter(
    self,
    story_id: str,
    chapter_number: int,
    selected_choice: str | None = None,
) -> dict:
    """
    Generate a new chapter for a story using Ollama LLM.

    Args:
        story_id: UUID of the story
        chapter_number: Number of the chapter to generate (1-based)
        selected_choice: User's selected continuation from previous chapter

    Returns:
        dict with chapter_id and status

    Raises:
        Retry: If Ollama API fails, retry with exponential backoff
    """
    # Placeholder implementation - will be completed in Stage 2
    logger.info(
        f"Generating chapter {chapter_number} for story {story_id} "
        f"with choice: {selected_choice}"
    )

    # TODO: Implement actual generation logic
    # 1. Get Story and previous chapters
    # 2. Build prompt using PromptBuilder
    # 3. Call OllamaClient to generate
    # 4. Parse response and save Chapter
    # 5. Update TaskStatus

    return {
        "story_id": story_id,
        "chapter_number": chapter_number,
        "status": "placeholder",
    }
