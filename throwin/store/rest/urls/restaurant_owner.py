"""Urls for restaurant owner related views."""
from django.urls import path

from store.rest.views.restaurant_owner import (
    StoreListCreateView,
    StaffListCreateView,
    StaffListByStoreView,
    RestaurantGachaHistoryView
)

urlpatterns = [
    path("/stores", StoreListCreateView.as_view(),
         name="store-list-create"
    ),
    path("/staff", StaffListCreateView.as_view(),
         name="staff-list-create"
    ),
    path("/store-staffs", StaffListByStoreView.as_view(),
         name="store-staff-list"
    ),
    path("/gacha-history", RestaurantGachaHistoryView.as_view(),
         name="gacha-history"
    ),
]