from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.rest.serializers.user_login import UserLoginSerializer
from drf_spectacular.utils import extend_schema


@extend_schema(
    request=UserLoginSerializer,
    responses={status.HTTP_200_OK: {"data": {"email": "str", "refresh": "str", "access": "str"}}},
)
class UserLogin(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get("user")

        # get token
        refresh = RefreshToken.for_user(user)
        response_data = {
            "msg": "Login Successful",
            "data": {
                "email": user.email,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }
        return Response(response_data, status=status.HTTP_200_OK)
