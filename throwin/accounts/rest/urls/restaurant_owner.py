"""URLS for restaurant owner related API views."""
from accounts.rest.views.restaurant_owner_login import RestaurantOwnerLogin

from django.urls import path

urlpatterns = [
    path(
        "/login",
        RestaurantOwnerLogin.as_view(),
        name="restaurant-owner-login"
    ),
]