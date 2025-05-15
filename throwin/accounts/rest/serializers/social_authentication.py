"""
    Serializer for Social sign in [Google, Facebook, Line, Apple]
"""
import requests
from django.conf import settings

from rest_framework import serializers

from accounts.utils import Google, register_social_user, Line


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
        first_name = google_user_data['given_name']
        last_name = google_user_data['family_name'] if google_user_data.get('family_name') else ''
        name = f"{first_name} {last_name}"
        provider = 'google'

        return register_social_user(provider, email, name)


# class LineSignInSerializer(serializers.Serializer):
#     access_token = serializers.CharField(min_length=6)
#
#     def validate_access_token(self, access_token):
#         response = requests.get(
#             'https://api.line.me/oauth2/v2.1/verify',
#             params={'access_token': access_token}
#         )
#         if response.status_code != 200:
#             raise serializers.ValidationError("Invalid access token.")
#
#         user_data = response.json()
#         user_id = user_data.get('sub')
#         if not user_id:
#             raise serializers.ValidationError("Invalid access token.")
#
#         email = user_data.get('email')
#         name = user_data.get('name')
#         provider = 'line'
#
#         return register_social_user(provider, email, name)


class LineSignInSerializer(serializers.Serializer):
    code = serializers.CharField()
    redirect_uri = serializers.CharField()

    def create(self, validated_data):
        code = validated_data.get('code')
        redirect_uri = validated_data.get('redirect_uri')

        # Exchange code for access token
        token_response = requests.post(
            'https://api.line.me/oauth2/v2.1/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
                'client_id': settings.LINE_CHANNEL_ID,
                'client_secret': settings.LINE_CHANNEL_SECRET,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if token_response.status_code != 200:
            raise serializers.ValidationError({'detail': 'Failed to obtain access token from LINE.'})

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        # Retrieve user profile
        profile_response = requests.get(
            'https://api.line.me/v2/profile',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if profile_response.status_code != 200:
            raise serializers.ValidationError({'detail': 'Failed to retrieve user profile from LINE.'})

        profile_data = profile_response.json()
        user_id = profile_data.get('userId')
        display_name = profile_data.get('displayName')
        email = profile_data.get('email')

        print("========== Line User Data ============")
        print("user id: ", user_id)
        print("display name: ", display_name)
        print("profile data: ", profile_data)
        email = profile_data.get('email')
        print("email: ", email)
        print("========== End Line User Data ============")


        if not user_id:
            raise serializers.ValidationError({'detail': 'Invalid user ID from LINE profile.'})

        # Construct pseudo-email if not available
        email = f"{user_id}@gmail.com"
        provider = 'line'

        # Call your social user register or authentication function.
        return register_social_user(provider, email, display_name)
