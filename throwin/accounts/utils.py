import uuid
import random
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from google.auth.transport import requests
from google.oauth2 import id_token

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken

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


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    pass


email_activation_token = EmailVerificationTokenGenerator()


def generate_email_activation_url(user):
    """Generate an activation url with user id and token """
    uid64 = urlsafe_base64_encode(force_bytes(user.id))
    token = user.token
    return f"{settings.FRONTEND_URL}/activate/{uid64}/{token}"


def generate_verification_token(user, new_email):
    """Generate a JWT access token with user id and new email"""
    token = AccessToken.for_user(user)
    token["new_email"] = new_email

    return str(token)


def generate_token():
    """Generate a token in the format: <6-char-prefix>-<UUID>."""

    # Generate a 6-character random prefix (lowercase letters and digits)
    prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    # Generate a UUID and convert it to a hex string (no dashes)
    uuid_part = uuid.uuid4().hex

    return f"{prefix}-{uuid_part}"


def generate_password_reset_token_url(user):
    uid64 = urlsafe_base64_encode(force_bytes(user.id))
    token = PasswordResetTokenGenerator().make_token(user)
    return f"{settings.FRONTEND_URL}/reset-password/{uid64}/{token}"
