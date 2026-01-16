"""URL configuration for the Interactive Story Generator project."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """Health check endpoint for Docker."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("accounts/", include("apps.accounts.urls")),
    path("api/", include("apps.api.urls")),
    path("api/v1/accounts/", include("apps.accounts.api.v1.urls")),
    path("", include("apps.stories.urls")),
]
