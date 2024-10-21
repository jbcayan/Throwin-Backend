"""URLs for user registration"""

from django.urls import path, include


urlpatterns = [
    path("/register", include("accounts.rest.urls.user_registration")),
    path("/login", include("accounts.rest.urls.user_login")),
    # path("/logout", include("accounts.rest.urls.user_logout")),
    path("/social", include("accounts.rest.urls.social_authentication")),
]
