"""URL configuration for API app."""

from django.urls import path

from .views import (
    ChapterDetailView,
    OllamaHealthView,
    StoryChaptersView,
    StoryDetailView,
    StoryListView,
    TaskStatusView,
)

app_name = "api"

urlpatterns = [
    path("stories/", StoryListView.as_view(), name="story_list"),
    path("story/<uuid:story_id>/", StoryDetailView.as_view(), name="story_detail"),
    path("story/<uuid:story_id>/chapters/", StoryChaptersView.as_view(), name="story_chapters"),
    path("chapter/<uuid:chapter_id>/", ChapterDetailView.as_view(), name="chapter_detail"),
    path("task-status/<uuid:task_id>/", TaskStatusView.as_view(), name="task_status"),
    path("health/ollama/", OllamaHealthView.as_view(), name="ollama_health"),
]
