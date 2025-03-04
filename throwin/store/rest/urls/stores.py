"""Urls for store"""

from django.urls import path

from store.rest.views.stores import StoreList, StoreDetail


urlpatterns = [
    path(
        "",
        StoreList.as_view(),
        name="store-list-create"
    ),
    path(
        "/<str:code>",
        StoreDetail.as_view(),
        name="store-detail-update-destroy"
    ),
]
