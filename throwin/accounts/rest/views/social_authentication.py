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
        return Response(serializer.data, status=status.HTTP_200_OK)
