"""Urls for restaurant owner related views."""
from django.urls import path

from store.rest.views.restaurant_owner import (
    StoreListCreateView,
    StaffListCreateView
)

urlpatterns = [
    path("/stores", StoreListCreateView.as_view()),
    path("/staff", StaffListCreateView.as_view()),
]