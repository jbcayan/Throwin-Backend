
from accounts.rest.views.user_registration import UserRegistration, CheckEmailAlreadyExists
from django.urls import path

urlpatterns = [
    path("/consumer", UserRegistration.as_view(), name="user-registration"),
    path("/check-email", CheckEmailAlreadyExists.as_view(), name="check-email"),
]
