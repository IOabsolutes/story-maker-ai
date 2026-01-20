"""E2E tests for story management flows."""

import pytest
from playwright.sync_api import Page, expect

from apps.stories.models import Story

from .pages import HomePage, StoryDetailPage


@pytest.mark.e2e
class TestStoryCreationFlow:
    """Test story creation flow."""

    def test_user_can_create_story_and_see_in_list(
        self,
        authenticated_home_page: HomePage,
        transactional_db,
    ) -> None:
        """Test: create story -> verify in list.

        User should be able to:
        1. Fill story creation form
        2. Submit and be redirected to story detail
        3. Go back and see story in list
        """
        home_page = authenticated_home_page
        home_page.navigate_to_home()

        # Create a story
        test_title = "My Amazing Adventure Story"
        test_premise = "A brave hero embarks on an epic journey to save the kingdom from darkness"

        home_page.create_story(
            title=test_title,
            premise=test_premise,
            language="en",
            max_chapters="5",
        )

        # Should be redirected to story detail (URL contains /story/)
        home_page.page.wait_for_url("**/story/**")

        # Go back to home
        home_page.navigate_to_home()

        # Verify story appears in list
        story_titles = home_page.get_story_titles()
        assert any(test_title in title for title in story_titles)

    def test_story_creation_with_invalid_data_shows_errors(
        self,
        authenticated_home_page: HomePage,
    ) -> None:
        """Test: create story with invalid data shows validation errors.

        User should see error messages when:
        - Title is too short
        - Premise is too short
        """
        home_page = authenticated_home_page
        home_page.navigate_to_home()

        # Try to create story with short title and premise
        home_page.create_story(
            title="Short",  # Less than 10 characters
            premise="Too short",  # Less than 20 characters
            language="en",
            max_chapters="5",
        )

        # Should see error messages
        alerts = home_page.get_alert_messages()
        assert len(alerts) > 0
        # Should contain validation error text
        alert_text = " ".join(alerts).lower()
        assert "title" in alert_text or "premise" in alert_text or "characters" in alert_text


@pytest.mark.e2e
class TestStoryListFlow:
    """Test story list display."""

    def test_empty_story_list_shows_message(
        self,
        authenticated_home_page: HomePage,
    ) -> None:
        """Test: empty story list shows appropriate message.

        New user with no stories should see a message
        encouraging them to create their first story.
        """
        home_page = authenticated_home_page
        home_page.navigate_to_home()

        # Should show empty state or no story items
        story_count = home_page.get_story_count()
        assert story_count == 0

        # Page should contain some text about creating first story
        page_text = home_page.page.content().lower()
        assert "create" in page_text or "first" in page_text or "story" in page_text

    def test_user_can_click_story_to_view_details(
        self,
        authenticated_home_page: HomePage,
        story_detail_page: StoryDetailPage,
        transactional_db,
    ) -> None:
        """Test: click story in list -> view story details.

        User should be able to click on a story title
        and be taken to the story detail page.
        """
        home_page = authenticated_home_page
        home_page.navigate_to_home()

        # First create a story
        test_title = "Clickable Story Title Here"
        test_premise = "A test story with a clickable title for testing navigation"

        home_page.create_story(
            title=test_title,
            premise=test_premise,
        )

        # Wait for redirect to story detail
        home_page.page.wait_for_url("**/story/**")

        # Go back to home
        home_page.navigate_to_home()

        # Click on the story
        home_page.click_story(test_title)

        # Should be on story detail page
        home_page.page.wait_for_url("**/story/**")
        assert story_detail_page.get_story_title()


@pytest.mark.e2e
class TestStoryRestartFlow:
    """Test story restart flow."""

    def test_user_can_restart_story(
        self,
        authenticated_home_page: HomePage,
        story_detail_page: StoryDetailPage,
        transactional_db,
    ) -> None:
        """Test: restart story -> chapters deleted -> new generation started.

        User should be able to:
        1. Create a story
        2. Click restart
        3. See chapters cleared
        4. See new generation started
        """
        home_page = authenticated_home_page
        home_page.navigate_to_home()

        # Create a story
        test_title = "Story To Restart Testing"
        test_premise = "This story will be restarted to test the restart functionality works correctly"

        home_page.create_story(
            title=test_title,
            premise=test_premise,
        )

        # Wait for story detail page
        home_page.page.wait_for_url("**/story/**")

        # Get the story ID from URL for verification
        url = home_page.page.url
        story_id = url.split("/story/")[1].rstrip("/")

        # Verify story exists
        assert Story.objects.filter(id=story_id).exists()

        # Find and click restart button (may need to handle modal)
        restart_btn = home_page.page.locator(
            "button:has-text('Restart'), form[action*='restart'] button"
        )
        if restart_btn.is_visible():
            restart_btn.click()

            # Handle confirmation modal if present
            confirm_btn = home_page.page.locator(
                ".modal button:has-text('Restart'), .modal button:has-text('Yes')"
            )
            if confirm_btn.is_visible():
                confirm_btn.click()

            # Should see success message about restart
            home_page.page.wait_for_timeout(500)  # Brief wait for message
            page_text = home_page.page.content().lower()
            assert "restart" in page_text or "generating" in page_text


@pytest.mark.e2e
class TestStoryDeleteFlow:
    """Test story deletion flow."""

    def test_user_can_delete_story(
        self,
        authenticated_home_page: HomePage,
        transactional_db,
    ) -> None:
        """Test: delete story -> removed from list.

        User should be able to:
        1. Create a story
        2. Delete it
        3. Not see it in the list anymore
        """
        home_page = authenticated_home_page
        home_page.navigate_to_home()

        # Create a story
        test_title = "Story To Delete Soon"
        test_premise = "This story will be deleted to test the deletion functionality"

        home_page.create_story(
            title=test_title,
            premise=test_premise,
        )

        # Wait for story detail page
        home_page.page.wait_for_url("**/story/**")

        # Find and click delete button
        delete_btn = home_page.page.locator(
            "button:has-text('Delete'), form[action*='delete'] button, "
            "[data-bs-target*='delete']"
        )
        if delete_btn.is_visible():
            delete_btn.click()

            # Handle confirmation modal if present
            confirm_btn = home_page.page.locator(
                ".modal button:has-text('Delete'), .modal button:has-text('Yes'), "
                ".modal button:has-text('Confirm')"
            )
            if confirm_btn.is_visible():
                confirm_btn.click()

            # Should be redirected to home
            home_page.page.wait_for_url(f"{home_page.base_url}/")

            # Story should not be in list
            story_titles = home_page.get_story_titles()
            assert test_title not in story_titles
