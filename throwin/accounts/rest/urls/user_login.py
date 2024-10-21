
from accounts.rest.views.user_login import UserLogin
from django.urls import path

urlpatterns = [
    path("", UserLogin.as_view(), name="user-registration"),
]
