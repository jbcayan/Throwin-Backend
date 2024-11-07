"""Serializer for password reset and password change."""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
User = get_user_model()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""

    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user is associated with this email address")
        return value


class PasswordChangeConfirmSerializer(serializers.Serializer):
    """Serializer for password change confirmation."""

    uid64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user_id = urlsafe_base64_decode(attrs["uid64"]).decode()
        token = attrs["token"]
        try:
            user = User.objects.get(pk=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise serializers.ValidationError("Token is invalid or expired")

            if attrs["new_password"] != attrs["confirm_password"]:
                raise serializers.ValidationError("Passwords do not match")

            attrs["user"] = user

        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")

        return attrs

    def save(self, **kwargs):
        password = self.validated_data["new_password"]
        user = self.validated_data["user"]

        user.set_password(password)
        user.save()
