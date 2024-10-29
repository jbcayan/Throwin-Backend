from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.rest.serializers.social_authentication import GoogleSignInSerializer
from drf_spectacular.utils import extend_schema


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
