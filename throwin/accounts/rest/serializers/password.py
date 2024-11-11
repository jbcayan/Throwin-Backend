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


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password change confirmation."""

    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")

        return attrs

    def save(self, user):
        password = self.validated_data["new_password"]
        user.set_password(password)
        user.save()


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError({
                "detail": "New password cannot be the same as the old password."
            })
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "detail": "Passwords do not match."
            })

        return attrs

    def save(self, user):
        password = self.validated_data["new_password"]
        if not user.check_password(self.validated_data["old_password"]):
            raise serializers.ValidationError({"detail": "Old password is incorrect."})
        user.set_password(password)
        user.save()
