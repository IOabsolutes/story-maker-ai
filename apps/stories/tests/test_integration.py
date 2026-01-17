"""Integration tests for full story generation flow."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from apps.stories.models import Chapter, Story, StoryStatus, TaskStatus, TaskStatusChoice
from apps.stories.services.ollama_client import OllamaResponse
from apps.stories.tasks import generate_chapter
from apps.stories.tests.factories import ChapterFactory, StoryFactory, UserFactory

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


class TestMockOllamaResponse:
    """Helper class with mock Ollama responses."""

    @staticmethod
    def regular_chapter_response() -> str:
        """Mock response for a regular chapter with choices."""
        return """[CHAPTER]
The hero stood at the crossroads, the ancient map clutched in their trembling hands.
To the north, dark storm clouds gathered over the Forbidden Mountains. To the east,
the sun-dappled path led toward the Whispering Woods where the elves were said to dwell.

The weight of the quest pressed heavily on their shoulders. The Oracle had been clear:
find the Crystal of Eternity before the next full moon, or all would be lost.
But which path would lead to salvation, and which to certain doom?

A rustling in the bushes made the hero freeze. Something was watching from the shadows.
[/CHAPTER]

[CHOICES]
1. Draw your sword and investigate the rustling in the bushes
2. Take the northern path toward the Forbidden Mountains
3. Follow the eastern path to the Whispering Woods
[/CHOICES]"""

    @staticmethod
    def final_chapter_response() -> str:
        """Mock response for a final chapter without choices."""
        return """[CHAPTER]
With a mighty swing, the hero shattered the Crystal of Darkness. A blinding light
erupted from the fragments, sweeping across the land like a tidal wave of pure energy.

The dark forces that had plagued the kingdom for a thousand years dissolved into
nothingness. The cursed creatures fled, and the corrupted lands began to heal.

As the light faded, the hero looked around at the world they had saved. The villagers
emerged from their hiding places, tears of joy streaming down their faces.

The hero smiled, knowing that peace had finally returned. Their quest was complete.

THE END
[/CHAPTER]"""


@pytest.fixture
def mock_ollama_regular():
    """Mock Ollama client to return a regular chapter response."""
    mock_response = OllamaResponse(
        text=TestMockOllamaResponse.regular_chapter_response(),
        model="llama3.2:3b",
        done=True,
    )
    with patch(
        "apps.stories.tasks.ollama_client.generate_sync",
        return_value=mock_response,
    ) as mock:
        yield mock


@pytest.fixture
def mock_ollama_final():
    """Mock Ollama client to return a final chapter response."""
    mock_response = OllamaResponse(
        text=TestMockOllamaResponse.final_chapter_response(),
        model="llama3.2:3b",
        done=True,
    )
    with patch(
        "apps.stories.tasks.ollama_client.generate_sync",
        return_value=mock_response,
    ) as mock:
        yield mock


@pytest.fixture
def mock_ollama_error():
    """Mock Ollama client to raise an error."""
    from common.exceptions import StoryGenerationError

    with patch(
        "apps.stories.tasks.ollama_client.generate_sync",
        side_effect=StoryGenerationError("Connection timeout"),
    ) as mock:
        yield mock


class TestGenerateChapterTask:
    """Tests for generate_chapter Celery task."""

    def test_generate_first_chapter(self, mock_ollama_regular):
        """Generate first chapter creates chapter with content and choices."""
        story = StoryFactory(max_chapters=5)

        # Call task directly (synchronous for testing)
        result = generate_chapter.apply(
            args=[str(story.id), 1, None],
            task_id=str(uuid.uuid4()),
        ).get()

        assert result["status"] == "success"
        assert result["chapter_number"] == 1

        # Verify chapter was created
        chapter = Chapter.objects.get(story=story, chapter_number=1)
        assert chapter.is_generated is True
        assert "crossroads" in chapter.content.lower()
        assert len(chapter.choices) == 3

        # Verify task status
        task_statuses = TaskStatus.objects.filter(story=story)
        assert task_statuses.count() == 1
        assert task_statuses.first().status == TaskStatusChoice.COMPLETED

    def test_generate_chapter_with_selected_choice(self, mock_ollama_regular):
        """Generate chapter with user's selected choice."""
        story = StoryFactory(max_chapters=5)
        ChapterFactory(
            story=story,
            chapter_number=1,
            is_generated=True,
            selected_choice="Explore the cave",
        )

        result = generate_chapter.apply(
            args=[str(story.id), 2, "Explore the cave"],
            task_id=str(uuid.uuid4()),
        ).get()

        assert result["status"] == "success"
        assert result["chapter_number"] == 2

        # Verify chapter 2 was created
        chapter2 = Chapter.objects.get(story=story, chapter_number=2)
        assert chapter2.is_generated is True

    def test_generate_final_chapter_completes_story(self, mock_ollama_final):
        """Generate final chapter marks story as completed."""
        story = StoryFactory(max_chapters=3, status=StoryStatus.IN_PROGRESS)
        ChapterFactory(story=story, chapter_number=1, is_generated=True)
        ChapterFactory(story=story, chapter_number=2, is_generated=True)

        result = generate_chapter.apply(
            args=[str(story.id), 3, "Fight the dragon"],
            task_id=str(uuid.uuid4()),
        ).get()

        assert result["status"] == "success"
        assert result["chapter_number"] == 3

        # Verify story is completed
        story.refresh_from_db()
        assert story.status == StoryStatus.COMPLETED

        # Verify final chapter has no choices
        chapter3 = Chapter.objects.get(story=story, chapter_number=3)
        assert chapter3.is_generated is True
        assert chapter3.choices == []  # Final chapter has no choices

    def test_generate_chapter_story_not_found(self, mock_ollama_regular):
        """Generate chapter for non-existent story returns error."""
        fake_story_id = str(uuid.uuid4())

        result = generate_chapter.apply(
            args=[fake_story_id, 1, None],
            task_id=str(uuid.uuid4()),
        ).get()

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    def test_generate_chapter_creates_task_status(self, mock_ollama_regular):
        """Generate chapter creates TaskStatus for tracking."""
        story = StoryFactory()
        task_id = uuid.uuid4()

        generate_chapter.apply(
            args=[str(story.id), 1, None],
            task_id=str(task_id),
        ).get()

        # Verify TaskStatus exists with correct task_id
        task_status = TaskStatus.objects.get(id=task_id)
        assert task_status.story == story
        assert task_status.chapter_number == 1
        assert task_status.status == TaskStatusChoice.COMPLETED


class TestFullStoryFlow:
    """Integration tests for complete story generation flow."""

    def test_full_story_flow_api_to_completion(
        self, authenticated_client, user, mock_ollama_regular, mock_ollama_final
    ):
        """Test complete flow: create story, generate chapters, complete."""
        # 1. Create story via API
        create_response = authenticated_client.post(
            "/api/v1/stories/",
            {
                "title": "Epic Adventure",
                "premise": "A hero embarks on a quest",
                "max_chapters": 2,
            },
            format="json",
        )
        assert create_response.status_code == 201
        story_id = create_response.data["id"]

        # Verify story created
        story = Story.objects.get(id=story_id)
        assert story.status == StoryStatus.IN_PROGRESS

        # 2. Generate first chapter (mock regular response)
        with patch(
            "apps.stories.tasks.ollama_client.generate_sync",
            return_value=OllamaResponse(
                text=TestMockOllamaResponse.regular_chapter_response(),
                model="llama3.2:3b",
                done=True,
            ),
        ):
            result1 = generate_chapter.apply(
                args=[str(story_id), 1, None],
                task_id=str(uuid.uuid4()),
            ).get()

        assert result1["status"] == "success"

        # Verify chapter 1 created
        chapter1 = Chapter.objects.get(story_id=story_id, chapter_number=1)
        assert chapter1.is_generated is True
        assert len(chapter1.choices) == 3

        # 3. Select a choice via API
        choice_response = authenticated_client.post(
            f"/api/v1/stories/{story_id}/chapters/{chapter1.id}/choice/",
            {"choice": chapter1.choices[0]},
            format="json",
        )
        assert choice_response.status_code == 200

        # Verify choice was selected
        chapter1.refresh_from_db()
        assert chapter1.selected_choice == chapter1.choices[0]

        # 4. Generate final chapter (mock final response)
        with patch(
            "apps.stories.tasks.ollama_client.generate_sync",
            return_value=OllamaResponse(
                text=TestMockOllamaResponse.final_chapter_response(),
                model="llama3.2:3b",
                done=True,
            ),
        ):
            result2 = generate_chapter.apply(
                args=[str(story_id), 2, chapter1.selected_choice],
                task_id=str(uuid.uuid4()),
            ).get()

        assert result2["status"] == "success"

        # 5. Verify story is completed
        story.refresh_from_db()
        assert story.status == StoryStatus.COMPLETED
        assert story.chapter_count == 2

        # Verify final chapter
        chapter2 = Chapter.objects.get(story_id=story_id, chapter_number=2)
        assert chapter2.is_generated is True
        assert chapter2.choices == []  # Final chapter


class TestTaskStatusPolling:
    """Tests for task status polling flow."""

    def test_task_status_lifecycle(self, authenticated_client, user, mock_ollama_regular):
        """Test TaskStatus transitions through lifecycle."""
        story = StoryFactory(user=user)
        task_id = uuid.uuid4()

        # Before task runs, no TaskStatus exists
        assert TaskStatus.objects.filter(id=task_id).count() == 0

        # Run task
        generate_chapter.apply(
            args=[str(story.id), 1, None],
            task_id=str(task_id),
        ).get()

        # TaskStatus should be COMPLETED
        task_status = TaskStatus.objects.get(id=task_id)
        assert task_status.status == TaskStatusChoice.COMPLETED

        # Poll via API
        response = authenticated_client.get(f"/api/task-status/{task_id}/")
        assert response.status_code == 200
        assert response.data["status"] == "completed"


class TestErrorHandling:
    """Tests for error handling in generation flow."""

    def test_generation_error_marks_task_failed(self):
        """When generation fails after all retries, task is marked failed."""
        from common.exceptions import StoryGenerationError

        story = StoryFactory()
        task_id = uuid.uuid4()

        # Mock to always fail
        with patch(
            "apps.stories.tasks.ollama_client.generate_sync",
            side_effect=StoryGenerationError("Connection refused"),
        ):
            # Run task - it will retry and eventually fail
            try:
                generate_chapter.apply(
                    args=[str(story.id), 1, None],
                    task_id=str(task_id),
                ).get()
            except StoryGenerationError:
                pass  # Expected

        # TaskStatus should be FAILED after retries exhausted
        task_status = TaskStatus.objects.get(id=task_id)
        assert task_status.status == TaskStatusChoice.FAILED
        assert "Connection refused" in task_status.error_message

    def test_story_not_found_no_task_status(self):
        """When story not found, no TaskStatus is created."""
        fake_story_id = str(uuid.uuid4())
        task_id = uuid.uuid4()

        result = generate_chapter.apply(
            args=[fake_story_id, 1, None],
            task_id=str(task_id),
        ).get()

        assert result["status"] == "error"
        # No TaskStatus created for non-existent story
        assert TaskStatus.objects.filter(id=task_id).count() == 0
