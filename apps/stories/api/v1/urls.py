"""URL configuration for stories API v1.

RESTful URL patterns following best practices:
- Plural nouns: /stories/, /chapters/
- UUID path parameters
- Nested resources limited to 2 levels
"""
from django.urls import path

from .views import (
    ChapterChoiceAPIView,
    ChapterListAPIView,
    StoryDetailAPIView,
    StoryListCreateAPIView,
)

urlpatterns = [
    path("", StoryListCreateAPIView.as_view(), name="api-story-list"),
    path("<uuid:story_id>/", StoryDetailAPIView.as_view(), name="api-story-detail"),
    path("<uuid:story_id>/chapters/", ChapterListAPIView.as_view(), name="api-chapter-list"),
    path(
        "<uuid:story_id>/chapters/<uuid:chapter_id>/choice/",
        ChapterChoiceAPIView.as_view(),
        name="api-chapter-choice",
    ),
]
