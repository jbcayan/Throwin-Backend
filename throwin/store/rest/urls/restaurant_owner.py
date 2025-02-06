"""Urls for restaurant owner related views."""
from django.urls import path

from store.rest.views.restaurant_owner import (
    StoreListCreateView,
    StaffListCreateView,
    StaffListByStoreView,
)

urlpatterns = [
    path("/stores", StoreListCreateView.as_view()),
    path("/staff", StaffListCreateView.as_view()),
    path("/store-staffs",
         StaffListByStoreView.as_view(),
         name="store-staff-list"
    ),
]