from django.urls import path, include
urlpatterns = [
    path("", include("store.rest.urls.stores")),
    path("/<str:store_code>/staff", include("store.rest.urls.store_staff")),
]