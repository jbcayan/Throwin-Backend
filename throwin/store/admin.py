from django.contrib import admin

from store.models import Store, Restaurant, StoreUser, RestaurantUser


# Register your models here.
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ["uid", "id", "name", "slug", "created_at"]
    search_fields = ["name"]
    list_filter = ["created_at"]


admin.site.register(Restaurant, RestaurantAdmin)


class RestaurantUserAdmin(admin.ModelAdmin):
    list_display = ["restaurant", "user", "role"]
    search_fields = ["restaurant__name", "user__name", "user__email"]
    list_filter = ["role"]


admin.site.register(RestaurantUser, RestaurantUserAdmin)


class StoreAdmin(admin.ModelAdmin):
    list_display = ["uid", "id", "name", "code", "created_at"]
    search_fields = ["name", "code"]
    list_filter = ["created_at"]


admin.site.register(Store, StoreAdmin)
