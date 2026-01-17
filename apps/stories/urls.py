"""URL configuration for stories app."""

from django.urls import path

from .views import (
    ChapterChooseView,
    HomeView,
    StoryDeleteView,
    StoryDetailView,
    StoryRestartView,
)

app_name = "stories"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("story/<uuid:story_id>/", StoryDetailView.as_view(), name="story_detail"),
    path("story/<uuid:story_id>/delete/", StoryDeleteView.as_view(), name="story_delete"),
    path("story/<uuid:story_id>/restart/", StoryRestartView.as_view(), name="story_restart"),
    path("chapter/<uuid:chapter_id>/choose/", ChapterChooseView.as_view(), name="chapter_choose"),
]
