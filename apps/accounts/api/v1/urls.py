"""URL configuration for accounts API v1."""

from django.urls import path

from .views import CurrentUserAPIView, RegisterAPIView

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="api-register"),
    path("me/", CurrentUserAPIView.as_view(), name="api-current-user"),
]
