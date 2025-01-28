"""Urls for store"""

from django.urls import path

from store.rest.views.stores import StoreList, StoreDetailUpdateDestroy


urlpatterns = [
    path(
        "",
        StoreList.as_view(),
        name="store-list-create"
    ),
    path(
        "/<str:code>",
        StoreDetailUpdateDestroy.as_view(),
        name="store-detail-update-destroy"
    ),
]
