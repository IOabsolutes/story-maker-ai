"""E2E test configuration and fixtures."""

import pytest
from django.contrib.auth.models import User
from playwright.sync_api import Page

from .pages import HomePage, LoginPage, StoryDetailPage


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """Configure browser context for all E2E tests.

    Args:
        browser_context_args: Default browser context arguments

    Returns:
        Updated browser context arguments
    """
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "locale": "en-US",
    }


@pytest.fixture
def e2e_user(transactional_db) -> User:
    """Create a test user for E2E tests.

    Args:
        transactional_db: Pytest-django fixture for database access

    Returns:
        Created User instance
    """
    user = User.objects.create_user(
        username="e2e_testuser",
        email="e2e@test.com",
        password="testpass123",
    )
    return user


@pytest.fixture
def e2e_user_credentials() -> dict[str, str]:
    """Return test user credentials.

    Returns:
        Dict with username and password
    """
    return {
        "username": "e2e_testuser",
        "password": "testpass123",
    }


@pytest.fixture
def login_page(page: Page, live_server) -> LoginPage:
    """Create LoginPage instance.

    Args:
        page: Playwright page fixture
        live_server: Django live server fixture

    Returns:
        LoginPage instance
    """
    return LoginPage(page, live_server.url)


@pytest.fixture
def home_page(page: Page, live_server) -> HomePage:
    """Create HomePage instance.

    Args:
        page: Playwright page fixture
        live_server: Django live server fixture

    Returns:
        HomePage instance
    """
    return HomePage(page, live_server.url)


@pytest.fixture
def story_detail_page(page: Page, live_server) -> StoryDetailPage:
    """Create StoryDetailPage instance.

    Args:
        page: Playwright page fixture
        live_server: Django live server fixture

    Returns:
        StoryDetailPage instance
    """
    return StoryDetailPage(page, live_server.url)


@pytest.fixture
def authenticated_page(
    page: Page,
    live_server,
    e2e_user: User,
    e2e_user_credentials: dict[str, str],
) -> Page:
    """Return a page logged in as test user.

    Args:
        page: Playwright page fixture
        live_server: Django live server fixture
        e2e_user: Test user fixture
        e2e_user_credentials: User credentials fixture

    Returns:
        Playwright page logged in as test user
    """
    login_page = LoginPage(page, live_server.url)
    login_page.navigate_to_login()
    login_page.login_and_wait(
        e2e_user_credentials["username"],
        e2e_user_credentials["password"],
    )
    return page


@pytest.fixture
def authenticated_home_page(
    authenticated_page: Page,
    live_server,
) -> HomePage:
    """Return HomePage with authenticated user.

    Args:
        authenticated_page: Page with logged in user
        live_server: Django live server fixture

    Returns:
        HomePage instance with authenticated session
    """
    return HomePage(authenticated_page, live_server.url)
