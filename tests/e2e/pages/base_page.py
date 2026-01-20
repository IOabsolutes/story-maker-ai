"""Base Page Object for E2E tests."""

from playwright.sync_api import Page


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page, base_url: str) -> None:
        """Initialize page object.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application (from live_server.url)
        """
        self.page = page
        self.base_url = base_url.rstrip("/")

    def navigate(self, path: str = "") -> None:
        """Navigate to a specific path.

        Args:
            path: Path relative to base URL (e.g., "/accounts/login/")
        """
        url = f"{self.base_url}{path}"
        self.page.goto(url)

    def get_current_url(self) -> str:
        """Get current page URL."""
        return self.page.url

    def wait_for_url(self, path: str, timeout: float = 5000) -> None:
        """Wait for navigation to a specific path.

        Args:
            path: Expected path (e.g., "/")
            timeout: Timeout in milliseconds
        """
        expected_url = f"{self.base_url}{path}"
        self.page.wait_for_url(expected_url, timeout=timeout)

    def get_text(self, selector: str) -> str:
        """Get text content of an element.

        Args:
            selector: CSS selector

        Returns:
            Text content of the element
        """
        return self.page.locator(selector).text_content() or ""

    def is_visible(self, selector: str) -> bool:
        """Check if element is visible.

        Args:
            selector: CSS selector

        Returns:
            True if element is visible
        """
        return self.page.locator(selector).is_visible()

    def click(self, selector: str) -> None:
        """Click on an element.

        Args:
            selector: CSS selector
        """
        self.page.locator(selector).click()

    def fill(self, selector: str, value: str) -> None:
        """Fill an input field.

        Args:
            selector: CSS selector
            value: Value to fill
        """
        self.page.locator(selector).fill(value)

    def get_alert_messages(self) -> list[str]:
        """Get all Bootstrap alert messages on the page.

        Returns:
            List of alert message texts
        """
        alerts = self.page.locator(".alert").all()
        return [alert.text_content() or "" for alert in alerts]
