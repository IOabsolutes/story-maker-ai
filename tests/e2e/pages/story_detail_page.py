"""Story Detail Page Object for E2E tests."""

from .base_page import BasePage


class StoryDetailPage(BasePage):
    """Page object for the story detail page."""

    # Selectors - Story Info
    STORY_TITLE = "h1, .story-title"
    STORY_PREMISE = ".story-premise, .card-text"
    STORY_STATUS = ".badge"
    PROGRESS_BAR = ".progress-bar"

    # Selectors - Chapters
    CHAPTER_CARD = ".chapter-card, .card"
    CHAPTER_CONTENT = ".chapter-content"
    CHAPTER_NUMBER = ".chapter-number, h5"

    # Selectors - Choice Form
    CHOICE_FORM = "form[action*='choose']"
    CHOICE_BUTTON = ".choice-btn, button[name='selected_choice']"
    USER_INPUT = "textarea[name='user_input'], input[name='user_input']"
    SUBMIT_CHOICE_BUTTON = "button[type='submit']"

    # Selectors - Actions
    DELETE_BUTTON = "button[data-bs-target*='delete'], a[href*='delete']"
    RESTART_BUTTON = "button[data-bs-target*='restart'], form[action*='restart'] button"
    BACK_LINK = "a[href='/']"

    # Selectors - Generation Status
    GENERATING_INDICATOR = "#generation-progress, .generating, .spinner"
    GENERATION_STATUS = ".generation-status"

    def get_story_title(self) -> str:
        """Get the story title.

        Returns:
            Story title text
        """
        return self.get_text(self.STORY_TITLE)

    def get_chapter_count(self) -> int:
        """Get number of chapters displayed.

        Returns:
            Number of chapter cards
        """
        return self.page.locator(self.CHAPTER_CONTENT).count()

    def get_chapter_contents(self) -> list[str]:
        """Get all chapter contents.

        Returns:
            List of chapter content texts
        """
        chapters = self.page.locator(self.CHAPTER_CONTENT).all()
        return [ch.text_content() or "" for ch in chapters]

    def get_last_chapter_content(self) -> str:
        """Get the last chapter's content.

        Returns:
            Content of the last chapter
        """
        chapters = self.page.locator(self.CHAPTER_CONTENT).all()
        if chapters:
            return chapters[-1].text_content() or ""
        return ""

    def has_choices(self) -> bool:
        """Check if choice buttons are displayed.

        Returns:
            True if choices are available
        """
        return self.page.locator(self.CHOICE_BUTTON).count() > 0

    def get_choices(self) -> list[str]:
        """Get available choice texts.

        Returns:
            List of choice button texts
        """
        buttons = self.page.locator(self.CHOICE_BUTTON).all()
        return [btn.text_content() or "" for btn in buttons]

    def select_choice(self, index: int = 0) -> None:
        """Select a choice by index.

        Args:
            index: Index of choice to select (0-based)
        """
        buttons = self.page.locator(self.CHOICE_BUTTON).all()
        if index < len(buttons):
            buttons[index].click()

    def enter_custom_choice(self, text: str) -> None:
        """Enter a custom continuation.

        Args:
            text: Custom text to enter
        """
        self.fill(self.USER_INPUT, text)
        self.click(self.SUBMIT_CHOICE_BUTTON)

    def is_generating(self) -> bool:
        """Check if a chapter is being generated.

        Returns:
            True if generation is in progress
        """
        return self.is_visible(self.GENERATING_INDICATOR)

    def wait_for_generation_complete(self, timeout: float = 60000) -> None:
        """Wait for chapter generation to complete.

        Args:
            timeout: Maximum time to wait in milliseconds
        """
        # Wait for generating indicator to disappear
        self.page.locator(self.GENERATING_INDICATOR).wait_for(
            state="hidden", timeout=timeout
        )

    def wait_for_chapter(self, chapter_number: int, timeout: float = 60000) -> None:
        """Wait for a specific chapter to appear.

        Args:
            chapter_number: Chapter number to wait for
            timeout: Maximum time to wait in milliseconds
        """
        # Wait for chapter content to appear
        self.page.locator(f"{self.CHAPTER_CONTENT}").nth(chapter_number - 1).wait_for(
            timeout=timeout
        )

    def restart_story(self) -> None:
        """Click restart button and confirm."""
        self.click(self.RESTART_BUTTON)
        # Handle confirmation modal if present
        confirm_btn = self.page.locator("button:has-text('Restart'), button:has-text('Confirm')")
        if confirm_btn.is_visible():
            confirm_btn.click()

    def delete_story(self) -> None:
        """Click delete button and confirm."""
        self.click(self.DELETE_BUTTON)
        # Handle confirmation modal if present
        confirm_btn = self.page.locator("button:has-text('Delete'), button:has-text('Confirm')")
        if confirm_btn.is_visible():
            confirm_btn.click()

    def go_back_home(self) -> None:
        """Navigate back to home page."""
        self.click(self.BACK_LINK)
