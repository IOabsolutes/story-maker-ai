"""Login Page Object for E2E tests."""

from .base_page import BasePage


class LoginPage(BasePage):
    """Page object for the login page."""

    URL = "/accounts/login/"

    # Selectors
    USERNAME_INPUT = "input[name='username']"
    PASSWORD_INPUT = "input[name='password']"
    SUBMIT_BUTTON = "button[type='submit']"
    REGISTER_LINK = "a[href*='register']"
    ERROR_MESSAGE = ".alert-danger, .errorlist"

    def navigate_to_login(self) -> None:
        """Navigate to login page."""
        self.navigate(self.URL)

    def login(self, username: str, password: str) -> None:
        """Perform login with given credentials.

        Args:
            username: Username to login with
            password: Password to login with
        """
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)

    def login_and_wait(self, username: str, password: str, expected_path: str = "/") -> None:
        """Perform login and wait for redirect.

        Args:
            username: Username to login with
            password: Password to login with
            expected_path: Expected path after successful login
        """
        self.login(username, password)
        self.wait_for_url(expected_path)

    def go_to_register(self) -> None:
        """Click on register link."""
        self.click(self.REGISTER_LINK)

    def has_error(self) -> bool:
        """Check if login error is displayed."""
        return self.is_visible(self.ERROR_MESSAGE)

    def is_on_login_page(self) -> bool:
        """Check if currently on login page."""
        return self.URL in self.get_current_url()
