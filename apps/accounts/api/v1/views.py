"""Views for accounts API v1."""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services import user_create

from .serializers import RegisterSerializer, UserSerializer


class RegisterAPIView(APIView):
    """API endpoint for user registration."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """
        Register a new user.

        Request body:
            username: str
            email: str
            password: str
            password_confirm: str

        Returns:
            201: User data
            400: Validation errors
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = user_create(
            username=serializer.validated_data["username"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class CurrentUserAPIView(APIView):
    """API endpoint for current user info."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Get current authenticated user info.

        Returns:
            200: User data
            401: Not authenticated
        """
        return Response(UserSerializer(request.user).data)
