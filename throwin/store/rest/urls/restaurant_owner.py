"""Urls for restaurant owner related views."""
from django.urls import path

from store.rest.views.restaurant_owner import (
    StoreListCreateView,
    StaffListCreateView,
    QRCodeGenerationView,
    StaffListByStoreView,
)

urlpatterns = [
    path("/stores", StoreListCreateView.as_view()),
    path("/staff", StaffListCreateView.as_view()),
    # path("/generate-qr",
    #      QRCodeGenerationView.as_view(),
    #      name="generate-qr"
    # ),
    path("/store-staffs",
         StaffListByStoreView.as_view(),
         name="store-staff-list"
    ),
]