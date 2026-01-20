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
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        stories = story_list(user=request.user)
        serializer = StoryListSerializer(stories, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
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
    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = "user"

    def get_object(self, story_id: str) -> Story:
        story = story_get(story_id=story_id, user=self.request.user)
        if story is None:
            raise NotFound("История не найдена")
        self.check_object_permissions(self.request, story)
        return story

    def get(self, request: Request, story_id: str) -> Response:
        story = self.get_object(story_id)
        serializer = StoryDetailSerializer(story)
        return Response(serializer.data)

    def delete(self, request: Request, story_id: str) -> Response:
        story = self.get_object(story_id)
        story.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChapterListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, story_id: str) -> Response:
        story = get_object_or_404(Story, id=story_id, user=request.user)
        chapters = chapter_list(story=story)
        serializer = ChapterSerializer(chapters, many=True)
        return Response(serializer.data)


class ChapterChoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, story_id: str, chapter_id: str) -> Response:
        story = get_object_or_404(Story, id=story_id, user=request.user)
        chapter = get_object_or_404(Chapter, id=chapter_id, story=story)

        serializer = ChapterChoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        chapter = chapter_select_choice(
            chapter=chapter,
            choice=serializer.validated_data["choice"],
        )

        return Response(ChapterSerializer(chapter).data)
