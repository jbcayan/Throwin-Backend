from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


def login_social_user(email, password):
    """
        Logs in a user and returns a refresh/access token pair.
    """
    user = authenticate(email=email, password=password)
    refresh = RefreshToken.for_user(user)

    data = {
        "msg": "Login Successful",
        "data": {
            "email": "",
            "name": user.name or "",
            "role": user.kind,
            "auth_provider": user.auth_provider,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    }
    # If auth_provider is Line the in data we aill append username instead of email
    if user.auth_provider == "line":
        data["data"]["username"] = user.username
    else:
        data["data"]["email"] = user.email
    return data
