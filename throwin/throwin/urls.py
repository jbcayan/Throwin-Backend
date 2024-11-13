
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Throwin Administration"
admin.site.site_title = "Throwin Admin Portal"
admin.site.index_title = "Welcome to Throwin Portal"

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/v1/auth", include("accounts.rest.urls")),
    path("api/v1/stores", include("store.rest.urls")),
    path('payment_service/', include('payment_service.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
    urlpatterns += [
        path("api/schema", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    ]

if settings.ENABLE_SILK:
    urlpatterns += [
        re_path(r"^silk", include("silk.urls", namespace="silk")),
    ]


