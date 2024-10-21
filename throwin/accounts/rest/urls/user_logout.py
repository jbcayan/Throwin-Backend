"""Urls for user logout"""

from django.urls import path

from accounts.rest.views.user_logout import UserLogout

urlpatterns = [
    path("", UserLogout.as_view(), name="user-logout"),
]