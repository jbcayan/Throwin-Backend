from django.conf import settings
from django.contrib.auth import get_user_model

from google.auth.transport import requests
from google.oauth2 import id_token

from rest_framework.exceptions import AuthenticationFailed

from common.utils import login_social_user

User = get_user_model()


class Google:
    @staticmethod
    def validate(self, access_token):
        """
        This method is used to validate the access token, 
        and we make it static so that it can be called from anywhere without creating an object
        """
        try:
            id_info = id_token.verify_oauth2_token(
                access_token, requests.Request(), settings.GOOGLE_CLIENT_ID
            )
            if 'accounts.google.com' not in id_info['iss']:
                raise ValueError('Wrong issuer.')
            return id_info
        except ValueError as e:
            raise AuthenticationFailed('Invalid credentials') from e


def register_social_user(provider, email, name):
    """
        Register a user with social login credentials if the user does not exist,
        or return a message to continue login with existing provider.
    """
    user = User.objects.filter(email=email)

    if user.exists():
        if user[0].auth_provider == provider:
            return login_social_user(email=email, password=settings.SOCIAL_AUTH_PASSWORD)
        else:
            raise AuthenticationFailed(
                detail=f'Please continue your login using {user[0].auth_provider}'
            )
    else:
        user = User.objects.create_user(
            email=email,
            name=name,
            auth_provider=provider,
        )
        user.set_password(settings.SOCIAL_AUTH_PASSWORD)
        user.save()

        return login_social_user(email=email, password=settings.SOCIAL_AUTH_PASSWORD)
