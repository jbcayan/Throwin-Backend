"""Serializer for user logout"""

from rest_framework import serializers

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

User = get_user_model()


class UserLogoutSerializer(serializers.Serializer):
    """Serializer for user logout"""

    refresh = serializers.CharField()

    default_error_messages = {
        "bad_token": ("Token is expired or invalid")
    }

    def validate(self, attrs):
        self.token = attrs["refresh"]
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            self.fail("bad_token")
