"""API views for the stories app."""

from typing import Any

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
    """List all stories for the authenticated user."""

    serializer_class = StoryListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter stories by current user."""
        return Story.objects.filter(user=self.request.user)


class StoryDetailView(generics.RetrieveAPIView):
    """Retrieve a single story with all chapters."""

    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "story_id"

    def get_queryset(self):
        """Filter stories by current user."""
        return Story.objects.filter(user=self.request.user)


class StoryChaptersView(generics.ListAPIView):
    """List all chapters for a story."""

    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter chapters by story and user ownership."""
        story_id = self.kwargs.get("story_id")
        return Chapter.objects.filter(
            story_id=story_id,
            story__user=self.request.user,
        )


class ChapterDetailView(generics.RetrieveAPIView):
    """Retrieve a single chapter."""

    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "chapter_id"

    def get_queryset(self):
        """Filter chapters by user ownership."""
        return Chapter.objects.filter(story__user=self.request.user)


class TaskStatusView(generics.RetrieveAPIView):
    """Retrieve task status for polling."""

    serializer_class = TaskStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "task_id"

    def get_queryset(self):
        """Filter task statuses by user ownership."""
        return TaskStatus.objects.filter(story__user=self.request.user)


class OllamaHealthView(APIView):
    """Health check endpoint for Ollama service."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Check Ollama availability."""
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
