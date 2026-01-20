from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwner(permissions.BasePermission):
    message = "Вы не являетесь владельцем этого объекта."

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        owner_field = getattr(view, "owner_field", "user")
        return getattr(obj, owner_field, None) == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    message = "Вы не являетесь владельцем этого объекта."

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        owner_field = getattr(view, "owner_field", "user")
        return getattr(obj, owner_field, None) == request.user
