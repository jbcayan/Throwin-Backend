from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from accounts.rest.serializers.social_authentication import (
    GoogleSignInSerializer,
    LineSignInSerializer,
)


@extend_schema(
    summary="Sign in with Google",
    request=GoogleSignInSerializer,
    description="Sign in with Google",
)
class GoogleSignIn(generics.GenericAPIView):
    serializer_class = GoogleSignInSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class LineSignIn(generics.GenericAPIView):
    serializer_class = LineSignInSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Use the create method to handle logic
            user_data = serializer.create(serializer.validated_data)
            return Response(user_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
