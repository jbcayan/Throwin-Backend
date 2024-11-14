"""Views for user registration"""

from django.conf import settings
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema

from rest_framework import generics, status
from rest_framework.response import Response

from accounts.models import TemporaryUser
from accounts.rest.serializers.user_registration import (
    UserRegisterSerializerWithEmail,
    CheckEmailAlreadyExistsSerializer,
    ResendActivationEmailSerializer,
)
from accounts.tasks import send_mail_task
from accounts.utils import generate_email_activation_url

User = get_user_model()


@extend_schema(
    summary="Consumer Registration by Email and Password",
    request=UserRegisterSerializerWithEmail,
    description="Consumer Registration, No Authentication Required",
)
class UserRegistration(generics.CreateAPIView):
    """View for user registration"""

    serializer_class = UserRegisterSerializerWithEmail

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        temp_user = serializer.save()

        activation_url = generate_email_activation_url(temp_user)

        # send email
        subject = "Activate Your Account"
        message = (
            f"Dear {temp_user.email},\n\n"
            f"Thank you for registering with {settings.SITE_NAME}! To complete your registration, "
            "please activate your account within the next 48 hours by clicking the link below:\n\n"
            f"{activation_url}\n\n"
            "If you did not initiate this registration, please ignore this email.\n\n"
            "Best regards,\n"
            f"The {settings.SITE_NAME} Team"
        )
        to_email = temp_user.email
        send_mail_task(subject, message, to_email)
        # send_mail_task.delay(subject, message, to_email)

        return Response({
            "msg": "User Created Successfully, Please check your email to activate your account in 48 hours."
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Check Email Already Exists",
    description="Check Email Already Exists, No Authorization Required",
    request=CheckEmailAlreadyExistsSerializer,
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


@extend_schema(
    summary="Resend Activation Email.",
    description="Resend Activation Email, No Authorization Required.",
    request=ResendActivationEmailSerializer,
)
class ResendActivationEmail(generics.GenericAPIView):
    serializer_class = ResendActivationEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        temp_user = TemporaryUser.objects.get(email=email)

        activation_url = generate_email_activation_url(temp_user)

        # send email
        subject = "Activate Your Account"
        message = (
            f"Dear {temp_user.email},\n\n"
            f"Thank you for registering with {settings.SITE_NAME}! To complete your registration, "
            "please activate your account within the next 48 hours by clicking the link below:\n\n"
            f"{activation_url}\n\n"
            "If you did not initiate this registration, please ignore this email.\n\n"
            "Best regards,\n"
            f"The {settings.SITE_NAME} Team"
        )
        to_email = temp_user.email
        send_mail_task(subject, message, to_email)
        # send_mail_task.delay(subject, message, to_email)

        return Response({
            "detail": "Email Sent Successfully"
        }, status=status.HTTP_200_OK)
