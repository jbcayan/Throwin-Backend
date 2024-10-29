"""Urls for user"""

from django.urls import path

from accounts.rest.views.user import (
    UserName,
    AccountActivation,
    EmailChangeRequest,
    VerifyEmailChange,
)

urlpatterns = [
    path(
        "/name",
        UserName.as_view(),
        name="user-name"
    ),
    path(
        "/acivate/<str:uidb64>/<str:token>",
        AccountActivation.as_view(),
        name="activate-account"
    ),
    path(
        "/email-change-reqquest",
        EmailChangeRequest.as_view(),
        name="email-change-request"
    ),
    path(
        "/email-verify",
        VerifyEmailChange.as_view(),
        name="verify-email-change"
    ),
]
