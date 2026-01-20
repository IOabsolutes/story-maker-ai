"""E2E tests for authentication flows."""

import pytest
from django.contrib.auth.models import User
from playwright.sync_api import Page, expect

from .pages import HomePage, LoginPage


@pytest.mark.e2e
class TestRegistrationFlow:
    """Test user registration flow."""

    def test_user_can_register_and_access_home(
        self,
        page: Page,
        live_server,
        transactional_db,
    ) -> None:
        """Test: signup -> access home page.

        User should be able to:
        1. Navigate to registration page
        2. Fill registration form
        3. Submit and be redirected to home
        4. See logged-in state
        """
        # Navigate to registration page
        page.goto(f"{live_server.url}/accounts/register/")

        # Fill registration form
        page.fill("input[name='username']", "newuser123")
        page.fill("input[name='email']", "newuser@test.com")
        page.fill("input[name='password1']", "securepass123!")
        page.fill("input[name='password2']", "securepass123!")

        # Submit form
        page.click("button[type='submit']")

        # Should be redirected to home
        page.wait_for_url(f"{live_server.url}/")

        # Verify user is logged in (logout link visible)
        expect(page.locator("a[href*='logout']")).to_be_visible()

        # Verify user was created in database
        assert User.objects.filter(username="newuser123").exists()

    def test_registration_with_existing_username_shows_error(
        self,
        page: Page,
        live_server,
        e2e_user: User,
    ) -> None:
        """Test: registration with existing username shows error.

        User should see an error when trying to register
        with a username that already exists.
        """
        page.goto(f"{live_server.url}/accounts/register/")

        # Try to register with existing username
        page.fill("input[name='username']", e2e_user.username)
        page.fill("input[name='email']", "another@test.com")
        page.fill("input[name='password1']", "securepass123!")
        page.fill("input[name='password2']", "securepass123!")
        page.click("button[type='submit']")

        # Should stay on registration page with error
        expect(page.locator(".errorlist, .alert-danger")).to_be_visible()


@pytest.mark.e2e
class TestLoginLogoutFlow:
    """Test login and logout flows."""

    def test_user_can_login_and_access_protected_page(
        self,
        login_page: LoginPage,
        home_page: HomePage,
        e2e_user: User,
        e2e_user_credentials: dict[str, str],
    ) -> None:
        """Test: login -> access protected page.

        User should be able to:
        1. Navigate to login page
        2. Enter credentials
        3. Be redirected to home
        4. See their logged-in state
        """
        # Navigate to login
        login_page.navigate_to_login()
        assert login_page.is_on_login_page()

        # Login
        login_page.login_and_wait(
            e2e_user_credentials["username"],
            e2e_user_credentials["password"],
        )

        # Should be on home page
        assert home_page.is_on_home_page()
        assert home_page.is_logged_in()

    def test_login_with_invalid_credentials_shows_error(
        self,
        login_page: LoginPage,
        transactional_db,
    ) -> None:
        """Test: login with invalid credentials shows error.

        User should see an error message when entering
        incorrect username or password.
        """
        login_page.navigate_to_login()

        # Try to login with invalid credentials
        login_page.login("wronguser", "wrongpass")

        # Should stay on login page with error
        assert login_page.is_on_login_page()
        assert login_page.has_error()

    def test_user_can_logout(
        self,
        authenticated_home_page: HomePage,
        login_page: LoginPage,
    ) -> None:
        """Test: logout -> redirected to login.

        Logged-in user should be able to:
        1. Click logout
        2. Be redirected to login page
        3. No longer see logged-in state
        """
        # Verify logged in
        assert authenticated_home_page.is_logged_in()

        # Logout
        authenticated_home_page.logout()

        # Should be redirected to login page
        # Wait for redirect
        authenticated_home_page.page.wait_for_url("**/accounts/login/**")
        assert login_page.is_on_login_page()

    def test_unauthenticated_user_redirected_to_login(
        self,
        page: Page,
        live_server,
        transactional_db,
    ) -> None:
        """Test: accessing protected page redirects to login.

        Unauthenticated user trying to access a protected page
        should be redirected to login.
        """
        # Try to access a story detail page directly
        page.goto(f"{live_server.url}/story/some-uuid/")

        # Should be redirected to login
        expect(page).to_have_url(lambda url: "login" in url)
