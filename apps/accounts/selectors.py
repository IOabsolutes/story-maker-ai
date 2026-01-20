from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

User = get_user_model()


def user_get_by_id(*, user_id: int) -> AbstractUser | None:
    return User.objects.filter(id=user_id).first()


def user_get_by_username(*, username: str) -> AbstractUser | None:
    return User.objects.filter(username=username).first()
