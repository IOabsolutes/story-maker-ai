"""Abstract model mixins."""

from django.conf import settings
from django.db import models


class TimestampMixin(models.Model):
    """Mixin that adds created_at and updated_at timestamps."""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
    )

    class Meta:
        abstract = True


class AuthorMixin(models.Model):
    """Mixin that adds author field linked to User model."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        verbose_name="Автор",
    )

    class Meta:
        abstract = True
