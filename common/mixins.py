"""ViewSet mixins for DRF."""

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.serializers import Serializer


class MultiSerializerMixin:
    """
    Use different serializers for different actions.

    Example:
        class MyViewSet(MultiSerializerMixin, ModelViewSet):
            serializer_class = DefaultSerializer
            serializer_action_classes = {
                'list': ListSerializer,
                'create': CreateSerializer,
            }
    """

    serializer_action_classes: dict[str, type[Serializer]] = {}
    serializer_class: type[Serializer]
    action: str

    def get_serializer_class(self) -> type[Serializer]:
        """Return serializer class based on current action."""
        return self.serializer_action_classes.get(self.action, self.serializer_class)


class ActionPermissionMixin:
    """
    Use different permissions for different actions.

    Example:
        class MyViewSet(ActionPermissionMixin, ModelViewSet):
            permission_classes = [IsAuthenticated]
            permission_action_classes = {
                'list': [AllowAny],
                'destroy': [IsAdminUser],
            }
    """

    permission_action_classes: dict[str, list[type[BasePermission]]] = {}
    permission_classes: list[type[BasePermission]]
    action: str

    def get_permissions(self) -> list[BasePermission]:
        """Return permissions based on current action."""
        permission_classes = self.permission_action_classes.get(
            self.action,
            self.permission_classes,
        )
        return [permission() for permission in permission_classes]


class OwnerQuerySetMixin:
    """
    Filter queryset to only show objects owned by current user.

    Example:
        class MyViewSet(OwnerQuerySetMixin, ModelViewSet):
            owner_field = "user"  # or "author"
    """

    owner_field: str = "user"
    request: Any

    def get_queryset(self) -> Any:
        """Filter queryset by owner field."""
        queryset = super().get_queryset()  # type: ignore[misc]
        if self.request.user.is_authenticated:
            return queryset.filter(**{self.owner_field: self.request.user})
        return queryset.none()
