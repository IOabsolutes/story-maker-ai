"""Views for stories API v1.

Following DRF best practices:
- Thin views that delegate to services layer
- Separate input/output serializers
- Explicit object-level permission checks
"""
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.stories.models import Chapter, Story
from apps.stories.selectors import chapter_list, story_get, story_list
from apps.stories.services import chapter_select_choice, story_create
from common.permissions import IsOwner

from .serializers import (
    ChapterChoiceSerializer,
    ChapterSerializer,
    StoryCreateSerializer,
    StoryDetailSerializer,
    StoryListSerializer,
)


class StoryListCreateAPIView(APIView):
    """API endpoint for listing and creating stories.

    GET /api/v1/stories/ - List user's stories
    POST /api/v1/stories/ - Create new story
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """List all stories for current user."""
        stories = story_list(user=request.user)
        serializer = StoryListSerializer(stories, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        """Create a new story."""
        serializer = StoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        story = story_create(
            user=request.user,
            title=serializer.validated_data["title"],
            premise=serializer.validated_data["premise"],
            language=serializer.validated_data.get("language", "ru"),
            max_chapters=serializer.validated_data.get("max_chapters", 10),
        )

        return Response(
            StoryDetailSerializer(story).data,
            status=status.HTTP_201_CREATED,
        )


class StoryDetailAPIView(APIView):
    """API endpoint for story details.

    GET /api/v1/stories/{id}/ - Get story with chapters
    DELETE /api/v1/stories/{id}/ - Delete story
    """

    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = "user"

    def get_object(self, story_id: str) -> Story:
        """Get story and check object-level permissions.

        Following DRF docs pattern for explicit permission check.
        """
        story = story_get(story_id=story_id, user=self.request.user)
        if story is None:
            raise NotFound("История не найдена")
        # Check object-level permissions (DRF best practice)
        self.check_object_permissions(self.request, story)
        return story

    def get(self, request: Request, story_id: str) -> Response:
        """Get story details with chapters."""
        story = self.get_object(story_id)
        serializer = StoryDetailSerializer(story)
        return Response(serializer.data)

    def delete(self, request: Request, story_id: str) -> Response:
        """Delete a story."""
        story = self.get_object(story_id)
        story.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChapterListAPIView(APIView):
    """API endpoint for listing chapters of a story.

    GET /api/v1/stories/{story_id}/chapters/ - List chapters
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, story_id: str) -> Response:
        """List all chapters for a story."""
        story = get_object_or_404(Story, id=story_id, user=request.user)
        chapters = chapter_list(story=story)
        serializer = ChapterSerializer(chapters, many=True)
        return Response(serializer.data)


class ChapterChoiceAPIView(APIView):
    """API endpoint for selecting a chapter choice.

    POST /api/v1/stories/{story_id}/chapters/{chapter_id}/choice/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, story_id: str, chapter_id: str) -> Response:
        """Select a choice for chapter continuation."""
        story = get_object_or_404(Story, id=story_id, user=request.user)
        chapter = get_object_or_404(Chapter, id=chapter_id, story=story)

        serializer = ChapterChoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        chapter = chapter_select_choice(
            chapter=chapter,
            choice=serializer.validated_data["choice"],
        )

        return Response(ChapterSerializer(chapter).data)
