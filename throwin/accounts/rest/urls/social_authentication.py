"""Urls for social authentication"""

from django.urls import path

from accounts.rest.views.social_authentication import GoogleSignIn

urlpatterns = [
    path(
        "/google",
        GoogleSignIn.as_view(),
        name="google-signin"
    ),
]