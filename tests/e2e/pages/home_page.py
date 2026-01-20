"""Home Page Object for E2E tests."""

from .base_page import BasePage


class HomePage(BasePage):
    """Page object for the home page (story creation and list)."""

    URL = "/"

    # Selectors - Story Creation Form
    TITLE_INPUT = "input[name='title']"
    PREMISE_INPUT = "textarea[name='premise']"
    LANGUAGE_SELECT = "select[name='language']"
    MAX_CHAPTERS_SELECT = "select[name='max_chapters']"
    CREATE_BUTTON = "button[type='submit']"

    # Selectors - Story List
    STORY_LIST = ".list-group"
    STORY_ITEM = ".list-group-item"
    STORY_TITLE = ".story-title, h5, h6"
    STORY_STATUS_BADGE = ".badge"

    # Selectors - Navigation
    NAVBAR = ".navbar"
    LOGOUT_LINK = "a[href*='logout']"
    LOGIN_LINK = "a[href*='login']"

    def navigate_to_home(self) -> None:
        """Navigate to home page."""
        self.navigate(self.URL)

    def create_story(
        self,
        title: str,
        premise: str,
        language: str = "ru",
        max_chapters: str = "10",
    ) -> None:
        """Fill and submit story creation form.

        Args:
            title: Story title
            premise: Story premise
            language: Language code (ru/en)
            max_chapters: Maximum number of chapters
        """
        self.fill(self.TITLE_INPUT, title)
        self.fill(self.PREMISE_INPUT, premise)
        self.page.locator(self.LANGUAGE_SELECT).select_option(language)
        self.page.locator(self.MAX_CHAPTERS_SELECT).select_option(max_chapters)
        self.click(self.CREATE_BUTTON)

    def get_story_count(self) -> int:
        """Get number of stories in the list.

        Returns:
            Number of stories displayed
        """
        return self.page.locator(self.STORY_ITEM).count()

    def get_story_titles(self) -> list[str]:
        """Get all story titles from the list.

        Returns:
            List of story titles
        """
        items = self.page.locator(self.STORY_ITEM).all()
        titles = []
        for item in items:
            title_elem = item.locator(self.STORY_TITLE)
            if title_elem.count() > 0:
                titles.append(title_elem.first.text_content() or "")
        return titles

    def click_story(self, title: str) -> None:
        """Click on a story by title.

        Args:
            title: Story title to click
        """
        self.page.locator(f"{self.STORY_ITEM}:has-text('{title}')").click()

    def is_logged_in(self) -> bool:
        """Check if user is logged in.

        Returns:
            True if logout link is visible
        """
        return self.is_visible(self.LOGOUT_LINK)

    def logout(self) -> None:
        """Click logout link."""
        self.click(self.LOGOUT_LINK)

    def is_on_home_page(self) -> bool:
        """Check if currently on home page."""
        return self.get_current_url().rstrip("/") == self.base_url
