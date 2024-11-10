"""Serializer for user logout"""

from rest_framework import serializers

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

User = get_user_model()


class UserLogoutSerializer(serializers.Serializer):
    """Serializer for user logout"""

    refresh = serializers.CharField()

    def validate(self, attrs):
        """
        Validate that the refresh token is provided
        """
        if not attrs["refresh"]:
            raise serializers.ValidationError("No refresh token provided")
        return attrs
