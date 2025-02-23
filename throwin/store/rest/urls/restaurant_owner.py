"""Urls for restaurant owner related views."""
from django.urls import path

from store.rest.views.restaurant_owner import (
    StoreListCreateView,
    StoreRetrieveUpdateDestroyView,
    StaffListCreateView,
    StaffListByStoreView,
    RestaurantGachaHistoryView,
    RestaurantOwnerChangeNameView,
    RestaurantOwnerChangeEmailRequestView,
    RestaurantOwnerDetailView
)

urlpatterns = [
    path("/stores", StoreListCreateView.as_view(),
         name="store-list-create"
    ),
    path("/stores/<str:uid>", StoreRetrieveUpdateDestroyView.as_view(),
         name="store-detail-update-destroy"
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
    path("/settings", RestaurantOwnerDetailView.as_view(),
         name="restaurant-owner-detail"
    ),
    path("/settings/change-name", RestaurantOwnerChangeNameView.as_view(),
         name="change-name"
    ),
    path("/settings/change-email-request", RestaurantOwnerChangeEmailRequestView.as_view(),
         name="change-email-request"
    ),
]