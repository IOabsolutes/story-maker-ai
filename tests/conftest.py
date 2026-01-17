"""Pytest configuration and fixtures."""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.fixture
def user(db) -> User:
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def other_user(db) -> User:
    """Create another test user for permission tests."""
    return User.objects.create_user(
        username="otheruser",
        email="other@example.com",
        password="testpass123",
    )


@pytest.fixture
def admin_user(db) -> User:
    """Create a superuser for admin tests."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def api_client() -> APIClient:
    """Return a DRF APIClient instance."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, user: User) -> APIClient:
    """Return an authenticated APIClient using force_authenticate."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def other_authenticated_client(api_client: APIClient, other_user: User) -> APIClient:
    """Return an APIClient authenticated as another user."""
    client = APIClient()
    client.force_authenticate(user=other_user)
    return client
