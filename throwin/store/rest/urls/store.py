"""Urls for store"""

from django.urls import path

from store.rest.views.store import StoreListCreate, StoreDetailUpdateDestroy


urlpatterns = [
    path(
        "",
        StoreListCreate.as_view(),
        name="store-list-create"
    ),
    path(
        "<str:code>",
        StoreDetailUpdateDestroy.as_view(),
        name="store-detail-update-destroy"
    ),
]
