"""Urls for social authentication"""

from django.urls import path

from accounts.rest.views.social_authentication import (
    GoogleSignIn,
    LineSignIn
)

urlpatterns = [
    path(
        "/google", GoogleSignIn.as_view(), name="google-signin"
    ),
    path(
        'social/line', LineSignIn.as_view(), name='line-signin'
    ),
]
