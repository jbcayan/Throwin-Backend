
from accounts.rest.views.user_registration import UserRegistration
from django.urls import path

urlpatterns = [
    path("/consumer", UserRegistration.as_view(), name="user-registration"),
]
