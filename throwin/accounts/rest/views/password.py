"""Views for password reset and password change"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework import generics, status
from rest_framework.response import Response

from accounts.rest.serializers.password import (
    PasswordResetRequestSerializer,
    PasswordChangeConfirmSerializer
)
from accounts.tasks import send_mail_task
from accounts.utils import generate_password_reset_token_url

User = get_user_model()


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = []

    def post(self, request):
        """Request password reset."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=serializer.data["email"])
        reset_url = generate_password_reset_token_url(user)

        # send email
        subject = "Password Reset Request"
        message = (
            f"Dear {user.username if user.username else user.email},\n\n"
            f"Please click the link below to reset your password:\n\n"
            f"{reset_url}\n\n"
            "If you did not initiate this password reset, please ignore this email.\n\n"
            "Best regards,\n"
            f"The {settings.SITE_NAME} Team"
        )
        to_email = user.email
        send_mail_task(subject, message, to_email)

        return Response({
            "detail": "Password reset link sent"
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordChangeConfirmSerializer

    def post(self, request, uid64, token):
        """Confirm password reset."""
        try:
            user_id = urlsafe_base64_decode(uid64).decode()
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({
                "detail": "User does not exist"
            }, status=status.HTTP_404_NOT_FOUND)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({
                "detail": "Token is invalid or expired"
            }, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)

        return Response({
            "detail": "Password reset successful"
        }, status=status.HTTP_200_OK)
