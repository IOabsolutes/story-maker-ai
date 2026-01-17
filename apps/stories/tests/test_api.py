"""Tests for stories API endpoints."""

import uuid

import pytest
from rest_framework import status

from apps.stories.models import StoryStatus
from apps.stories.tests.factories import (
    ChapterFactory,
    StoryFactory,
    TaskStatusFactory,
)

pytestmark = pytest.mark.django_db


class TestStoryListCreateAPIView:
    """Tests for GET/POST /api/v1/stories/"""

    endpoint = "/api/v1/stories/"

    def test_list_requires_auth(self, api_client):
        """Unauthenticated requests should return 403."""
        response = api_client.get(self.endpoint)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_stories_empty(self, authenticated_client):
        """Returns empty list when user has no stories."""
        response = authenticated_client.get(self.endpoint)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_list_stories(self, authenticated_client, user):
        """Returns list of user's stories."""
        story1 = StoryFactory(user=user, title="Story 1")
        story2 = StoryFactory(user=user, title="Story 2")

        response = authenticated_client.get(self.endpoint)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        titles = {s["title"] for s in response.data}
        assert titles == {"Story 1", "Story 2"}

    def test_list_stories_own_only(self, authenticated_client, user, other_user):
        """Returns only user's own stories, not others'."""
        StoryFactory(user=user, title="My Story")
        StoryFactory(user=other_user, title="Other's Story")

        response = authenticated_client.get(self.endpoint)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["title"] == "My Story"

    def test_create_story_success(self, authenticated_client, user):
        """Create story with valid data returns 201."""
        data = {
            "title": "New Adventure",
            "premise": "A brave hero sets out on a journey",
        }
        response = authenticated_client.post(self.endpoint, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Adventure"
        assert response.data["premise"] == "A brave hero sets out on a journey"
        assert response.data["status"] == StoryStatus.IN_PROGRESS

    def test_create_story_with_language(self, authenticated_client):
        """Create story with custom language."""
        data = {
            "title": "English Story",
            "premise": "A tale in English",
            "language": "en",
        }
        response = authenticated_client.post(self.endpoint, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["language"] == "en"

    def test_create_story_with_max_chapters(self, authenticated_client):
        """Create story with custom max_chapters."""
        data = {
            "title": "Short Story",
            "premise": "A brief tale",
            "max_chapters": 5,
        }
        response = authenticated_client.post(self.endpoint, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["max_chapters"] == 5

    def test_create_story_validation_error_missing_title(self, authenticated_client):
        """Create story without title returns 400."""
        data = {"premise": "No title provided"}
        response = authenticated_client.post(self.endpoint, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "title" in response.data

    def test_create_story_validation_error_missing_premise(self, authenticated_client):
        """Create story without premise returns 400."""
        data = {"title": "No Premise"}
        response = authenticated_client.post(self.endpoint, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "premise" in response.data


class TestStoryDetailAPIView:
    """Tests for GET/DELETE /api/v1/stories/{story_id}/"""

    def get_endpoint(self, story_id):
        return f"/api/v1/stories/{story_id}/"

    def test_get_story_requires_auth(self, api_client):
        """Unauthenticated requests should return 403."""
        story = StoryFactory()
        response = api_client.get(self.get_endpoint(story.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_story_success(self, authenticated_client, user):
        """Get story returns story with chapters."""
        story = StoryFactory(user=user, title="My Story")
        ChapterFactory(story=story, chapter_number=1)
        ChapterFactory(story=story, chapter_number=2)

        response = authenticated_client.get(self.get_endpoint(story.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "My Story"
        assert len(response.data["chapters"]) == 2

    def test_get_story_not_found(self, authenticated_client):
        """Get non-existent story returns 404."""
        fake_id = uuid.uuid4()
        response = authenticated_client.get(self.get_endpoint(fake_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_story_forbidden(self, authenticated_client, other_user):
        """Cannot get another user's story."""
        story = StoryFactory(user=other_user)
        response = authenticated_client.get(self.get_endpoint(story.id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_story_success(self, authenticated_client, user):
        """Delete own story returns 204."""
        story = StoryFactory(user=user)
        response = authenticated_client.delete(self.get_endpoint(story.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_story_forbidden(self, authenticated_client, other_user):
        """Cannot delete another user's story."""
        story = StoryFactory(user=other_user)
        response = authenticated_client.delete(self.get_endpoint(story.id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_story_not_found(self, authenticated_client):
        """Delete non-existent story returns 404."""
        fake_id = uuid.uuid4()
        response = authenticated_client.delete(self.get_endpoint(fake_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestChapterListAPIView:
    """Tests for GET /api/v1/stories/{story_id}/chapters/"""

    def get_endpoint(self, story_id):
        return f"/api/v1/stories/{story_id}/chapters/"

    def test_list_chapters_requires_auth(self, api_client):
        """Unauthenticated requests should return 403."""
        story = StoryFactory()
        response = api_client.get(self.get_endpoint(story.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_chapters_empty(self, authenticated_client, user):
        """Returns empty list when story has no chapters."""
        story = StoryFactory(user=user)
        response = authenticated_client.get(self.get_endpoint(story.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_list_chapters(self, authenticated_client, user):
        """Returns list of chapters for story."""
        story = StoryFactory(user=user)
        ChapterFactory(story=story, chapter_number=1, content="Chapter 1 content")
        ChapterFactory(story=story, chapter_number=2, content="Chapter 2 content")

        response = authenticated_client.get(self.get_endpoint(story.id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_list_chapters_ordered(self, authenticated_client, user):
        """Chapters are ordered by chapter_number."""
        story = StoryFactory(user=user)
        ChapterFactory(story=story, chapter_number=3)
        ChapterFactory(story=story, chapter_number=1)
        ChapterFactory(story=story, chapter_number=2)

        response = authenticated_client.get(self.get_endpoint(story.id))
        assert response.status_code == status.HTTP_200_OK
        numbers = [c["chapter_number"] for c in response.data]
        assert numbers == [1, 2, 3]

    def test_list_chapters_forbidden(self, authenticated_client, other_user):
        """Cannot list chapters of another user's story."""
        story = StoryFactory(user=other_user)
        response = authenticated_client.get(self.get_endpoint(story.id))
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestChapterChoiceAPIView:
    """Tests for POST /api/v1/stories/{story_id}/chapters/{chapter_id}/choice/"""

    def get_endpoint(self, story_id, chapter_id):
        return f"/api/v1/stories/{story_id}/chapters/{chapter_id}/choice/"

    def test_select_choice_requires_auth(self, api_client):
        """Unauthenticated requests should return 403."""
        story = StoryFactory()
        chapter = ChapterFactory(story=story)
        response = api_client.post(
            self.get_endpoint(story.id, chapter.id),
            {"choice": "Option 1"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_select_choice_success(self, authenticated_client, user):
        """Select a valid choice returns updated chapter."""
        story = StoryFactory(user=user)
        chapter = ChapterFactory(
            story=story,
            chapter_number=1,
            choices=["Go left", "Go right"],
            selected_choice=None,
        )

        response = authenticated_client.post(
            self.get_endpoint(story.id, chapter.id),
            {"choice": "Go left"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["selected_choice"] == "Go left"

    def test_select_choice_custom_input(self, authenticated_client, user):
        """Select a custom user input as choice."""
        story = StoryFactory(user=user)
        chapter = ChapterFactory(
            story=story,
            chapter_number=1,
            selected_choice=None,
        )

        custom_input = "I want to explore the mysterious cave"
        response = authenticated_client.post(
            self.get_endpoint(story.id, chapter.id),
            {"choice": custom_input},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["selected_choice"] == custom_input

    def test_select_choice_validation_error(self, authenticated_client, user):
        """Select choice with empty string returns 400."""
        story = StoryFactory(user=user)
        chapter = ChapterFactory(story=story)

        response = authenticated_client.post(
            self.get_endpoint(story.id, chapter.id),
            {"choice": ""},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_select_choice_missing_field(self, authenticated_client, user):
        """Select choice without choice field returns 400."""
        story = StoryFactory(user=user)
        chapter = ChapterFactory(story=story)

        response = authenticated_client.post(
            self.get_endpoint(story.id, chapter.id),
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_select_choice_chapter_not_found(self, authenticated_client, user):
        """Select choice for non-existent chapter returns 404."""
        story = StoryFactory(user=user)
        fake_chapter_id = uuid.uuid4()

        response = authenticated_client.post(
            self.get_endpoint(story.id, fake_chapter_id),
            {"choice": "Option 1"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_select_choice_story_not_found(self, authenticated_client, user):
        """Select choice for non-existent story returns 404."""
        story = StoryFactory(user=user)
        chapter = ChapterFactory(story=story)
        fake_story_id = uuid.uuid4()

        response = authenticated_client.post(
            self.get_endpoint(fake_story_id, chapter.id),
            {"choice": "Option 1"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_select_choice_forbidden(self, authenticated_client, other_user):
        """Cannot select choice for another user's story."""
        story = StoryFactory(user=other_user)
        chapter = ChapterFactory(story=story)

        response = authenticated_client.post(
            self.get_endpoint(story.id, chapter.id),
            {"choice": "Option 1"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTaskStatusView:
    """Tests for GET /api/task-status/{task_id}/"""

    def get_endpoint(self, task_id):
        return f"/api/task-status/{task_id}/"

    def test_get_task_status_requires_auth(self, api_client):
        """Unauthenticated requests should return 403."""
        task_status = TaskStatusFactory()
        response = api_client.get(self.get_endpoint(task_status.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_task_status_success(self, authenticated_client, user):
        """Get task status returns status data."""
        story = StoryFactory(user=user)
        task_status = TaskStatusFactory(story=story, status="processing")

        response = authenticated_client.get(self.get_endpoint(task_status.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "processing"

    def test_get_task_status_not_found(self, authenticated_client):
        """Get non-existent task status returns 404."""
        fake_id = uuid.uuid4()
        response = authenticated_client.get(self.get_endpoint(fake_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_task_status_forbidden(self, authenticated_client, other_user):
        """Cannot get task status for another user's story."""
        story = StoryFactory(user=other_user)
        task_status = TaskStatusFactory(story=story)

        response = authenticated_client.get(self.get_endpoint(task_status.id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_task_status_completed_with_no_error(self, authenticated_client, user):
        """Completed task has no error message."""
        story = StoryFactory(user=user)
        task_status = TaskStatusFactory(
            story=story,
            status="completed",
            error_message="",
        )

        response = authenticated_client.get(self.get_endpoint(task_status.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "completed"
        assert response.data["error_message"] == ""

    def test_get_task_status_failed_with_error(self, authenticated_client, user):
        """Failed task has error message."""
        story = StoryFactory(user=user)
        task_status = TaskStatusFactory(
            story=story,
            status="failed",
            error_message="Connection timeout",
        )

        response = authenticated_client.get(self.get_endpoint(task_status.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "failed"
        assert response.data["error_message"] == "Connection timeout"
