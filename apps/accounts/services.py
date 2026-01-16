"""Account services for user operations."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

User = get_user_model()


def user_create(*, username: str, email: str, password: str) -> AbstractUser:
    """
    Create a new user account.

    Args:
        username: Unique username
        email: User email address
        password: Plain text password (will be hashed)

    Returns:
        Created user instance
    """
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )
    return user
