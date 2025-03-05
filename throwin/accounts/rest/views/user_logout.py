"""Logout View"""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

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
        refresh_token = serializer.validated_data["refresh"]

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                "detail": "Logout successful"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "detail": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
