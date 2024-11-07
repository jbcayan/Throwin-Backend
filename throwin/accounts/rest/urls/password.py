"""URls for password reset and password change"""

from django.urls import path

from accounts.rest.views.password import (
    PasswordResetRequestView,
    PasswordResetConfirmView
)

urlpatterns = [
    path(
        "/reset-request",
        PasswordResetRequestView.as_view(),
        name="password-reset-request"
    ),
    path(
        "/reset-confirm/<str:uid64>/<str:token>",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm"
    ),
]