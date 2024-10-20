"""URLs for user registration"""

from django.urls import path, include


urlpatterns = [
    path("/register", include("accounts.rest.urls.user_registration")),
]
