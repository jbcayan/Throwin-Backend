from django.urls import path, include
urlpatterns = [
    path("", include("store.rest.urls.store")),
    path("/<str:store_code>/stuff", include("store.rest.urls.store_stuff")),
]