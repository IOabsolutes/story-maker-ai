from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

User = get_user_model()


def user_create(*, username: str, email: str, password: str) -> AbstractUser:
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )
    return user
