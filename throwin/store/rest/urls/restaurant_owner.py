"""Urls for restaurant owner related views."""
from django.urls import path

from store.rest.views.restaurant_owner import RestaurantStoresView

urlpatterns = [
    path("/stores", RestaurantStoresView.as_view()),
]