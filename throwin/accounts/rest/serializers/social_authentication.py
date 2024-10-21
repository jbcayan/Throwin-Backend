"""
    Serializer for Social sign in [Google, Facebook, Line, Apple]
"""

from rest_framework import serializers
from accounts.utils import Google, register_social_user
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status


class GoogleSignInSerializer(serializers.Serializer):
    """
    Serializer for Google sign in
    """
    access_token = serializers.CharField(min_length=6)

    def validate_access_token(self, access_token):
        google_user_data = Google.validate(self, access_token)
        try:
            user_id = google_user_data['sub']
        except:
            raise serializers.ValidationError({
                "detail": "Invalid access token."
            }, code="authorization")

        if google_user_data['aud'] != settings.GOOGLE_CLIENT_ID:
            raise serializers.ValidationError({
                "detail": "could not verify user."
            }, code="authorization")

        print("="*30)
        print(google_user_data)
        print("="*30)

        email = google_user_data['email']
        name = google_user_data['given_name'] + ' ' + google_user_data['family_name']
        provider = 'google'

        return register_social_user(provider, email, name)
