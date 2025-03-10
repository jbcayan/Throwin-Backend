"""
    Serializer for Social sign in [Google, Facebook, Line, Apple]
"""
import requests
from django.conf import settings

from rest_framework import serializers

from accounts.utils import Google, register_social_user


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

        email = google_user_data['email']
        name = google_user_data['given_name'] + ' ' + google_user_data['family_name']
        # profile_image = google_user_data.get('picture')  # Get the profile image URL
        provider = 'google'

        return register_social_user(provider, email, name)


class LineSignInSerializer(serializers.Serializer):
    access_token = serializers.CharField(min_length=6)

    def validate_access_token(self, access_token):
        response = requests.get(
            'https://api.line.me/oauth2/v2.1/verify',
            params={'access_token': access_token}
        )
        if response.status_code != 200:
            raise serializers.ValidationError("Invalid access token.")

        user_data = response.json()
        user_id = user_data.get('sub')
        if not user_id:
            raise serializers.ValidationError("Invalid access token.")

        email = user_data.get('email')
        name = user_data.get('name')
        provider = 'line'

        return register_social_user(provider, email, name)