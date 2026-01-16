"""Custom permission classes."""

from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwner(permissions.BasePermission):
    """
    Permission that checks if user is the owner of the object.

    The view can specify the owner field name via `owner_field` attribute.
    Defaults to "user".
    """

    message = "Вы не являетесь владельцем этого объекта."

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        """Check if request user is the owner of the object."""
        owner_field = getattr(view, "owner_field", "user")
        return getattr(obj, owner_field, None) == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow read access to all, write access only to owner.

    The view can specify the owner field name via `owner_field` attribute.
    Defaults to "user".
    """

    message = "Вы не являетесь владельцем этого объекта."

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        """Check permissions: read for all, write for owner only."""
        if request.method in permissions.SAFE_METHODS:
            return True
        owner_field = getattr(view, "owner_field", "user")
        return getattr(obj, owner_field, None) == request.user
