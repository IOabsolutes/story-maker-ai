"""Prompt builder for story generation."""

import logging
import re
from typing import Any

from apps.stories.models import Chapter, Story

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builder for constructing prompts for story generation."""

    # System prompts by language
    SYSTEM_PROMPTS = {
        "ru": """Ты - талантливый писатель интерактивных историй. Твоя задача - создавать увлекательные главы истории на русском языке.

Правила:
1. Пиши живо и увлекательно, используя богатый язык
2. Каждая глава должна быть 300-500 слов
3. Заканчивай главу интригующим моментом
4. ОБЯЗАТЕЛЬНО предлагай ровно 3 варианта продолжения в конце
5. Не используй ненормативную лексику и откровенный контент

ВАЖНО: Варианты продолжения ОБЯЗАТЕЛЬНЫ. Без них ответ неполный.

Формат ответа (СТРОГО соблюдай):
[CHAPTER]
Текст главы здесь...
[/CHAPTER]

[CHOICES]
1. Первый вариант продолжения
2. Второй вариант продолжения
3. Третий вариант продолжения
[/CHOICES]""",
        "en": """You are a talented interactive story writer. Your task is to create engaging story chapters in English.

Rules:
1. Write vividly and engagingly, using rich language
2. Each chapter should be 300-500 words
3. End the chapter with an intriguing moment
4. ALWAYS provide exactly 3 continuation options at the end
5. No profanity or explicit content

IMPORTANT: Continuation options are MANDATORY. Without them the response is incomplete.

Response format (STRICTLY follow):
[CHAPTER]
Chapter text here...
[/CHAPTER]

[CHOICES]
1. First continuation option
2. Second continuation option
3. Third continuation option
[/CHOICES]""",
    }

    FINAL_CHAPTER_PROMPTS = {
        "ru": """Это ФИНАЛЬНАЯ глава истории. Заверши историю красивым и удовлетворительным финалом.
НЕ предлагай варианты продолжения - история должна закончиться.

Формат ответа:
[CHAPTER]
Финальный текст истории здесь...
[/CHAPTER]""",
        "en": """This is the FINAL chapter of the story. Conclude the story with a beautiful and satisfying ending.
DO NOT provide continuation options - the story must end.

Response format:
[CHAPTER]
Final story text here...
[/CHAPTER]""",
    }

    def build_chapter_prompt(
        self,
        story: Story,
        previous_chapters: list[Chapter],
        selected_choice: str | None,
        chapter_number: int,
    ) -> str:
        """
        Build a prompt for generating a new chapter.

        Args:
            story: The Story object
            previous_chapters: List of previous Chapter objects
            selected_choice: User's selected continuation from previous chapter
            chapter_number: Number of the chapter to generate

        Returns:
            Complete prompt string for the LLM
        """
        language = story.language
        is_final = chapter_number >= story.max_chapters

        # Start with system prompt
        if is_final:
            system_prompt = self.FINAL_CHAPTER_PROMPTS.get(language, self.FINAL_CHAPTER_PROMPTS["en"])
        else:
            system_prompt = self.SYSTEM_PROMPTS.get(language, self.SYSTEM_PROMPTS["en"])

        # Build context
        parts = [system_prompt, "", "---", ""]

        # Add story premise
        if language == "ru":
            parts.append(f"Замысел истории: {story.premise}")
        else:
            parts.append(f"Story premise: {story.premise}")
        parts.append("")

        # Add previous chapters summary (to save tokens)
        if previous_chapters:
            if language == "ru":
                parts.append("Краткое содержание предыдущих глав:")
            else:
                parts.append("Summary of previous chapters:")

            for chapter in previous_chapters[-3:]:  # Only last 3 chapters
                summary = self._summarize_chapter(chapter)
                parts.append(f"- Глава {chapter.chapter_number}: {summary}")
            parts.append("")

        # Add selected choice
        if selected_choice:
            if language == "ru":
                parts.append(f"Выбранное продолжение: {selected_choice}")
            else:
                parts.append(f"Chosen continuation: {selected_choice}")
            parts.append("")

        # Add instruction
        if language == "ru":
            parts.append(f"Напиши главу {chapter_number}.")
        else:
            parts.append(f"Write chapter {chapter_number}.")

        return "\n".join(parts)

    def _summarize_chapter(self, chapter: Chapter, max_length: int = 200) -> str:
        """
        Create a brief summary of a chapter for context.

        Args:
            chapter: The Chapter object
            max_length: Maximum summary length

        Returns:
            Brief summary string
        """
        content = chapter.content.strip()
        if len(content) <= max_length:
            return content

        # Truncate and add ellipsis
        return content[:max_length].rsplit(" ", 1)[0] + "..."

    def parse_response(self, response: str) -> dict[str, Any]:
        """
        Parse LLM response to extract chapter content and choices.

        Args:
            response: Raw response from LLM

        Returns:
            Dict with 'content' and 'choices' keys
        """
        content = ""
        choices: list[str] = []

        # Extract chapter content
        if "[CHAPTER]" in response and "[/CHAPTER]" in response:
            start = response.find("[CHAPTER]") + len("[CHAPTER]")
            end = response.find("[/CHAPTER]")
            content = response[start:end].strip()

        # Extract choices
        if "[CHOICES]" in response:
            # Handle both [/CHOICES] and missing closing tag
            start = response.find("[CHOICES]") + len("[CHOICES]")
            if "[/CHOICES]" in response:
                end = response.find("[/CHOICES]")
            else:
                end = len(response)
            choices_text = response[start:end].strip()

            for line in choices_text.split("\n"):
                line = line.strip()
                if line and line[0].isdigit():
                    # Remove numbering (1. 2. 3.)
                    choice = line.lstrip("0123456789.").strip()
                    if choice:
                        choices.append(choice)

        # Fallback if [CHAPTER] parsing fails - use response but REMOVE [CHOICES] section
        if not content:
            content = response.strip()
            if "[CHOICES]" in content:
                choices_start = content.find("[CHOICES]")
                if "[/CHOICES]" in content:
                    choices_end = content.find("[/CHOICES]") + len("[/CHOICES]")
                    content = content[:choices_start].strip() + content[choices_end:].strip()
                else:
                    content = content[:choices_start].strip()

        content = content.replace("[CHAPTER]", "").replace("[/CHAPTER]", "")
        content = content.replace("[CHOICES]", "").replace("[/CHOICES]", "")
        content = content.strip()

        # Also clean "Как вы хотели бы продолжить историю?" and similar phrases
        # that sometimes appear before choices
        for phrase in [
            "Как вы хотели бы продолжить историю?",
            "How would you like to continue the story?",
            "What happens next?",
            "Что будет дальше?",
        ]:
            content = content.replace(phrase, "").strip()

        # Fallback: extract choices from content when AI doesn't use tags
        if not choices and content:
            choices, content = self._extract_choices_fallback(content)

        return {
            "content": content,
            "choices": choices[:3],  # Max 3 choices
        }

    def _extract_choices_fallback(self, content: str) -> tuple[list[str], str]:
        """
        Extract choices from content when AI doesn't use [CHOICES] tags.

        Looks for numbered lists (1. xxx, 2. xxx, 3. xxx) at the end of content,
        optionally preceded by marker phrases like "Варианты:" or "Options:".

        Args:
            content: The chapter content that may contain inline choices

        Returns:
            Tuple of (extracted choices list, cleaned content)
        """
        choices: list[str] = []

        # Markers that typically precede choices (case-insensitive)
        marker_patterns = [
            r"(?:Варианты|Выберите|Выбор|Options|Choose|Choices)[\s:]*",
            r"(?:Что (?:вы )?(?:будете|хотите) делать|What (?:will you|do you want to) do)\??\s*",
            r"(?:Как (?:вы )?(?:хотите |желаете )?продолжить|How (?:would you like to |do you want to )?continue)\??\s*",
        ]

        # Try to find a marker followed by numbered list
        for marker_pattern in marker_patterns:
            # Pattern: marker + numbered list at end of content
            full_pattern = (
                rf"({marker_pattern})"
                rf"(?:\n|\s)*"
                rf"((?:\d[.)]\s*.+?(?:\n|$))+)"
                rf"\s*$"
            )
            match = re.search(full_pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                choices_block = match.group(2)
                choices = self._parse_numbered_list(choices_block)
                if choices:
                    # Remove the entire choices section from content
                    content = content[: match.start()].strip()
                    return choices, content

        # Fallback: look for numbered list at the very end (no marker)
        # Must have at least 2 items to be considered choices
        numbered_pattern = r"((?:\n\s*\d[.)]\s*.+)+)\s*$"
        match = re.search(numbered_pattern, content)
        if match:
            choices_block = match.group(1)
            potential_choices = self._parse_numbered_list(choices_block)
            if len(potential_choices) >= 2:
                choices = potential_choices
                content = content[: match.start()].strip()
                return choices, content

        return choices, content

    def _parse_numbered_list(self, text: str) -> list[str]:
        """
        Parse a numbered list from text.

        Args:
            text: Text containing numbered items (1. xxx, 2) xxx, etc.)

        Returns:
            List of extracted items without numbering
        """
        choices: list[str] = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                # Remove numbering (1. 2. 3. or 1) 2) 3))
                choice = re.sub(r"^\d+[.)]\s*", "", line).strip()
                if choice:
                    choices.append(choice)
        return choices
