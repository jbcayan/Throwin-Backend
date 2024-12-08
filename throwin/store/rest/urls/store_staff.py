from django.urls import path

from store.rest.views.store_stuff import (
    StoreStuffList
)

urlpatterns = [
    path(
        "/list",
        StoreStuffList.as_view(),
        name="store-stuff-list"
    ),
]