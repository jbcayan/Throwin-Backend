from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


def login_social_user(email, password):
    """
        Logs in a user and returns a refresh/access token pair.
    """
    user = authenticate(email=email, password=password)
    refresh = RefreshToken.for_user(user)
    return {
        "msg": "Login Successful",
        "data": {
            "email": user.email,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        },
    }
