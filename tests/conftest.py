"""Pytest configuration and fixtures."""

import pytest
from django.contrib.auth.models import User


@pytest.fixture
def user(db) -> User:
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )
