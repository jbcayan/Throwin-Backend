from django.contrib import admin
from store.models import Store, Restaurant, StoreUser, RestaurantUser


class RestaurantAdmin(admin.ModelAdmin):
    """Admin configuration for Restaurant model."""
    list_display = ["uid", "id", "name", "slug", "restaurant_owner", "sales_agent", "created_at"]
    search_fields = ["name", "slug", "restaurant_owner__name", "sales_agent__name"]
    list_filter = ["created_at"]
    readonly_fields = ["slug"]

    def get_queryset(self, request):
        """Optimize queries for restaurant admin."""
        return super().get_queryset(request).select_related("restaurant_owner", "sales_agent")


admin.site.register(Restaurant, RestaurantAdmin)


class RestaurantUserAdmin(admin.ModelAdmin):
    """Admin configuration for RestaurantUser model."""
    list_display = ["uid", "id", "restaurant", "user", "role", "created_at"]
    search_fields = ["restaurant__name", "user__name", "user__email"]
    list_filter = ["role", "created_at"]

    def get_queryset(self, request):
        """Optimize queries for restaurant user admin."""
        return super().get_queryset(request).select_related("restaurant", "user")


admin.site.register(RestaurantUser, RestaurantUserAdmin)


class StoreAdmin(admin.ModelAdmin):
    """Admin configuration for Store model."""
    list_display = ["uid", "id", "name", "code", "restaurant", "status", "created_at"]
    search_fields = ["name","uid", "code", "restaurant__name"]
    list_filter = ["restaurant", "created_at"]

    def get_queryset(self, request):
        """Optimize queries for store admin."""
        return super().get_queryset(request).select_related("restaurant")


admin.site.register(Store, StoreAdmin)


class StoreUserAdmin(admin.ModelAdmin):
    """Admin configuration for StoreUser model."""
    list_display = ["uid", "id", "role", "store", "user", "created_at"]
    search_fields = ["store__name", "store__code", "user__name", "user__email"]
    list_filter = ["store", "user", "role", "created_at"]

    def get_queryset(self, request):
        """Optimize queries for store user admin."""
        return super().get_queryset(request).select_related("store", "user")


admin.site.register(StoreUser, StoreUserAdmin)
