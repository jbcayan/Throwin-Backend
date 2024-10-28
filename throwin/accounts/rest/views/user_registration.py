"""Views for user registration"""
from rest_framework.response import Response
from accounts.rest.serializers.user_registration import (
    UserRegisterSerializerWithEmail,
    CheckEmailAlreadyExistsSerializer,
)
from rest_framework import generics, status
from drf_spectacular.utils import extend_schema

from django.contrib.auth import get_user_model

User = get_user_model()


@extend_schema(
    request=UserRegisterSerializerWithEmail,
    responses={status.HTTP_201_CREATED: {"msg": "User Created Successfully"}},
    description="Consumer Registration",
    methods=["POST"],
)
class UserRegistration(generics.CreateAPIView):
    """View for user registration"""

    serializer_class = UserRegisterSerializerWithEmail

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "detail": "User Created Successfully",
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    responses={status.HTTP_200_OK: {"detail": "Email Available"}},
    description="Check Email Already Exists",
    methods=["POST"],
)
class CheckEmailAlreadyExists(generics.GenericAPIView):
    """View for check email already exists"""

    serializer_class = CheckEmailAlreadyExistsSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # email = serializer.validated_data.get("email")
        # if User.objects.filter(email=email).exists():
        #     return Response({"detail": "Email Already Exists"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Email Available"}, status=status.HTTP_200_OK)
