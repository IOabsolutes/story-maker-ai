from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.stories.models import Chapter, Story, TaskStatus
from apps.stories.services import ollama_client

from .serializers import (
    ChapterSerializer,
    StoryListSerializer,
    StorySerializer,
    TaskStatusSerializer,
)


class StoryListView(generics.ListAPIView):
    serializer_class = StoryListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Story.objects.filter(user=self.request.user)


class StoryDetailView(generics.RetrieveAPIView):
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "story_id"

    def get_queryset(self):
        return Story.objects.filter(user=self.request.user)


class StoryChaptersView(generics.ListAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        story_id = self.kwargs.get("story_id")
        return Chapter.objects.filter(
            story_id=story_id,
            story__user=self.request.user,
        )


class ChapterDetailView(generics.RetrieveAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "chapter_id"

    def get_queryset(self):
        return Chapter.objects.filter(story__user=self.request.user)


class TaskStatusView(generics.RetrieveAPIView):
    serializer_class = TaskStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "task_id"

    def get_queryset(self):
        return TaskStatus.objects.filter(story__user=self.request.user)


class OllamaHealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        is_available = ollama_client.is_available()

        if is_available:
            return Response({
                "status": "healthy",
                "ollama_available": True,
                "model": settings.OLLAMA_MODEL,
            })
        return Response(
            {
                "status": "unhealthy",
                "ollama_available": False,
                "error": "Connection refused",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
