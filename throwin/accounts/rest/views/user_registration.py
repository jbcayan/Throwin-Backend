"""Views for user registration"""

from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema

from rest_framework import generics, status
from rest_framework.response import Response

from accounts.rest.serializers.user_registration import (
    UserRegisterSerializerWithEmail,
    CheckEmailAlreadyExistsSerializer,
)
from accounts.tasks import send_mail_task
from accounts.utils import generate_email_activation_url

User = get_user_model()


@extend_schema(
    summary="Consumer Registration by Email and Password",
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

        activation_url = generate_email_activation_url(user)
        print("Activation URL: ", activation_url)

        # send email
        subject = "Activate Your Account"
        message = f"Please click the link below to activate your account. {activation_url}"
        to_email = user.email
        send_mail_task(subject, message, to_email)
        print("Email sent!")

        return Response({
            "detail": "User Created Successfully",
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Check Email Already Exists",
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

        return Response({
            "detail": "Email Available"
        }, status=status.HTTP_200_OK)
