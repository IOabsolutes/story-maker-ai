"""Account selectors for user queries."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

User = get_user_model()


def user_get_by_id(*, user_id: int) -> AbstractUser | None:
    """
    Get user by ID.

    Args:
        user_id: User primary key

    Returns:
        User instance or None if not found
    """
    return User.objects.filter(id=user_id).first()


def user_get_by_username(*, username: str) -> AbstractUser | None:
    """
    Get user by username.

    Args:
        username: Username to search for

    Returns:
        User instance or None if not found
    """
    return User.objects.filter(username=username).first()
