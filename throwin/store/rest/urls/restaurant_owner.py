"""Urls for restaurant owner related views."""
from django.urls import path

from store.rest.views.restaurant_owner import (
    StoreListCreateView,
)

urlpatterns = [
    path("/stores", StoreListCreateView.as_view()),

]