from django.urls import path, include
urlpatterns = [
    path("/<str:store_code>/stuff", include("store.rest.urls.store_stuff")),
]