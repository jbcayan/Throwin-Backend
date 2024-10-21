"""Logout View"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from accounts.rest.serializers.user_logout import UserLogoutSerializer


@extend_schema(
    request=UserLogoutSerializer,
    responses={status.HTTP_204_NO_CONTENT: None},
    description="Logout API",
    methods=["POST"],
)
class UserLogout(APIView):
    """Logout View"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserLogoutSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
