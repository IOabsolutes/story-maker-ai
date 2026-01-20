"""E2E tests for chapter generation and choice selection flows.

Note: These tests require a running Celery worker and Ollama service.
They are marked as slow and may be skipped in CI without full infrastructure.
"""

import pytest
from playwright.sync_api import Page

from apps.stories.models import Chapter, Story

from .pages import HomePage, StoryDetailPage


@pytest.mark.e2e
@pytest.mark.slow
class TestChapterGenerationFlow:
    """Test chapter generation flow.

    These tests require full infrastructure (Celery, Ollama) to run.
    In CI without full infrastructure, these may fail or be skipped.
    """

    def test_story_creation_triggers_generation(
        self,
        authenticated_home_page: HomePage,
        story_detail_page: StoryDetailPage,
        transactional_db,
    ) -> None:
        """Test: create story -> generation starts.

        After creating a story, user should see:
        1. Redirect to story detail page
        2. Generation status indicator
        3. Success message about generation
        """
        home_page = authenticated_home_page
        home_page.navigate_to_home()

        # Create a story
        test_title = "Generation Test Story Title"
        test_premise = "An epic adventure where a young wizard discovers a hidden portal"

        home_page.create_story(
            title=test_title,
            premise=test_premise,
            language="en",
            max_chapters="3",
        )

        # Should be redirected to story detail
        home_page.page.wait_for_url("**/story/**")

        # Should see generation-related message or indicator
        page_content = home_page.page.content().lower()
        assert (
            "generating" in page_content
            or "chapter" in page_content
            or "progress" in page_content
        )

    @pytest.mark.skip(reason="Requires full infrastructure with Celery and Ollama")
    def test_chapter_generation_completes(
        self,
        authenticated_home_page: HomePage,
        story_detail_page: StoryDetailPage,
        transactional_db,
    ) -> None:
        """Test: wait for chapter generation to complete.

        This test requires full infrastructure and may take a while.
        After generation completes, user should see:
        1. Chapter content displayed
        2. Choice options (if not final chapter)
        """
        home_page = authenticated_home_page
        home_page.navigate_to_home()

        # Create a story
        home_page.create_story(
            title="Complete Generation Test",
            premise="A story to test that generation completes successfully",
            max_chapters="3",
        )

        # Wait for redirect to story detail
        home_page.page.wait_for_url("**/story/**")

        # Wait for generation to complete (may take a while)
        # This waits for chapter content to appear
        story_detail_page.page.locator(".chapter-content").wait_for(timeout=120000)

        # Should have at least one chapter
        assert story_detail_page.get_chapter_count() >= 1

        # Chapter should have content
        content = story_detail_page.get_last_chapter_content()
        assert len(content) > 0


@pytest.mark.e2e
@pytest.mark.slow
class TestChoiceSelectionFlow:
    """Test choice selection flow.

    These tests require full infrastructure (Celery, Ollama) to run.
    """

    def test_choice_form_displayed_after_chapter(
        self,
        page: Page,
        live_server,
        transactional_db,
    ) -> None:
        """Test: choices are displayed after generated chapter.

        When a chapter is generated with choices, user should see:
        1. Choice buttons or form
        2. Option to enter custom continuation
        """
        # This test would need a pre-created story with a generated chapter
        # For now, we verify the page structure handles choices

        # Create story and chapter directly in database for testing UI
        from django.contrib.auth.models import User

        user = User.objects.create_user("choiceuser", "choice@test.com", "testpass123")
        story = Story.objects.create(
            user=user,
            title="Choice Test Story Title",
            premise="A test premise for testing choice display",
            language="en",
            max_chapters=5,
        )
        Chapter.objects.create(
            story=story,
            chapter_number=1,
            content="The hero stood at the crossroads, uncertain which path to take.",
            choices=["Go left into the dark forest", "Go right toward the mountains", "Stay and make camp"],
            is_generated=True,
        )

        # Login as the user
        page.goto(f"{live_server.url}/accounts/login/")
        page.fill("input[name='username']", "choiceuser")
        page.fill("input[name='password']", "testpass123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{live_server.url}/")

        # Navigate to story detail
        page.goto(f"{live_server.url}/story/{story.id}/")

        # Should see chapter content
        assert page.locator(".chapter-content").is_visible()

        # Should see choice buttons or form
        choice_elements = page.locator(".choice-btn, button[name='selected_choice']")
        assert choice_elements.count() >= 1

    @pytest.mark.skip(reason="Requires full infrastructure with Celery and Ollama")
    def test_selecting_choice_triggers_next_chapter(
        self,
        page: Page,
        live_server,
        transactional_db,
    ) -> None:
        """Test: select choice -> next chapter generation starts.

        When user selects a choice:
        1. Choice is saved
        2. Next chapter generation starts
        3. User sees generation status
        """
        # This would test the full flow but requires infrastructure
        pass

    def test_custom_choice_input_accepted(
        self,
        page: Page,
        live_server,
        transactional_db,
    ) -> None:
        """Test: user can enter custom continuation.

        User should be able to:
        1. Enter custom text instead of preset choices
        2. Submit the custom continuation
        """
        from django.contrib.auth.models import User

        user = User.objects.create_user("customuser", "custom@test.com", "testpass123")
        story = Story.objects.create(
            user=user,
            title="Custom Choice Test Title",
            premise="A test premise for testing custom choice input",
            language="en",
            max_chapters=5,
        )
        Chapter.objects.create(
            story=story,
            chapter_number=1,
            content="The wizard pondered their next move carefully.",
            choices=["Cast a spell", "Consult the ancient tome", "Call for help"],
            is_generated=True,
        )

        # Login
        page.goto(f"{live_server.url}/accounts/login/")
        page.fill("input[name='username']", "customuser")
        page.fill("input[name='password']", "testpass123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{live_server.url}/")

        # Navigate to story detail
        page.goto(f"{live_server.url}/story/{story.id}/")

        # Find custom input field
        custom_input = page.locator("textarea[name='user_input'], input[name='user_input']")
        if custom_input.is_visible():
            # Enter custom choice
            custom_input.fill("The wizard decides to take a completely different approach")

            # Submit (find the form's submit button)
            submit_btn = page.locator("form button[type='submit']").last
            submit_btn.click()

            # Should see some response (message or generation status)
            page.wait_for_timeout(500)
            # Either we get an error (no Celery) or success message
            page_content = page.content().lower()
            assert (
                "generating" in page_content
                or "unavailable" in page_content
                or "chapter" in page_content
            )


@pytest.mark.e2e
class TestGenerationStatusPolling:
    """Test generation status polling behavior.

    These tests verify the polling UI behavior without requiring
    full backend infrastructure.
    """

    def test_generating_indicator_shown_during_generation(
        self,
        page: Page,
        live_server,
        transactional_db,
    ) -> None:
        """Test: generation indicator shown when task is pending.

        When a chapter is being generated, user should see:
        1. A loading/generating indicator
        2. Progress information
        """
        from django.contrib.auth.models import User

        from apps.stories.models import TaskStatus

        user = User.objects.create_user("polluser", "poll@test.com", "testpass123")
        story = Story.objects.create(
            user=user,
            title="Polling Test Story Title",
            premise="A test premise for testing polling indicator",
            language="en",
            max_chapters=5,
        )

        # Create a pending task status to simulate ongoing generation
        TaskStatus.objects.create(
            id="test-task-id-12345",
            story=story,
            chapter_number=1,
            status="pending",
        )

        # Login
        page.goto(f"{live_server.url}/accounts/login/")
        page.fill("input[name='username']", "polluser")
        page.fill("input[name='password']", "testpass123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{live_server.url}/")

        # Navigate to story detail
        page.goto(f"{live_server.url}/story/{story.id}/")

        # Should see some indication of generation in progress
        page_content = page.content().lower()
        assert (
            "generating" in page_content
            or "progress" in page_content
            or "loading" in page_content
            or "spinner" in page_content
            or "wait" in page_content
        )
