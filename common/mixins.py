from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.serializers import Serializer


class MultiSerializerMixin:
    serializer_action_classes: dict[str, type[Serializer]] = {}
    serializer_class: type[Serializer]
    action: str

    def get_serializer_class(self) -> type[Serializer]:
        return self.serializer_action_classes.get(self.action, self.serializer_class)


class ActionPermissionMixin:
    permission_action_classes: dict[str, list[type[BasePermission]]] = {}
    permission_classes: list[type[BasePermission]]
    action: str

    def get_permissions(self) -> list[BasePermission]:
        permission_classes = self.permission_action_classes.get(
            self.action,
            self.permission_classes,
        )
        return [permission() for permission in permission_classes]


class OwnerQuerySetMixin:
    owner_field: str = "user"
    request: Any

    def get_queryset(self) -> Any:
        queryset = super().get_queryset()  # type: ignore[misc]
        if self.request.user.is_authenticated:
            return queryset.filter(**{self.owner_field: self.request.user})
        return queryset.none()
