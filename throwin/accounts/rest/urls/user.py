"""Urls for user"""

from django.urls import path

from accounts.rest.views.user import UserName

urlpatterns = [
    path("/name", UserName.as_view(), name="user-name"),
]