from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.choices import UserKind
from accounts.rest.serializers.user_login import UserLoginSerializer


@extend_schema(
    summary="Login API by email and password",
    request=UserLoginSerializer,
    responses={status.HTTP_200_OK: {"data": {"email": "str", "refresh": "str", "access": "str"}}},
    description="Login API",
    methods=["POST"],
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
                "name": user.name or "",
                "role": user.kind,
                "auth_provider": user.auth_provider,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }

        if user.auth_provider == "line":
            response_data["data"]["username"] = user.username
        else:
            response_data["data"]["email"] = user.email

        if user.kind == UserKind.SALES_AGENT:
            response_data["data"]["agency_code"] = user.profile.agency_code
        return Response(response_data, status=status.HTTP_200_OK)
