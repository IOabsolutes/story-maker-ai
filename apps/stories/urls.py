"""URL configuration for stories app."""

from django.urls import path

from .views import HomeView, StoryDetailView

app_name = "stories"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("story/<uuid:story_id>/", StoryDetailView.as_view(), name="story_detail"),
]
