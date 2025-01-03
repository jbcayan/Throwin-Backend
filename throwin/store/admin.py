from django.contrib import admin

from store.models import Store, Restaurant


# Register your models here.
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ["uid", "id", "name", "slug", "created_at"]
    search_fields = ["name"]
    list_filter = ["created_at"]


admin.site.register(Restaurant, RestaurantAdmin)


class StoreAdmin(admin.ModelAdmin):
    list_display = ["uid", "id", "name", "code", "created_at"]
    search_fields = ["name", "code"]
    list_filter = ["created_at"]


admin.site.register(Store, StoreAdmin)

# class StoreUserAdmin(admin.ModelAdmin):
#     list_display = ["id", "uid", "user", "store", "role", "is_default", "created_at"]
#     search_fields = ["user__email", "store__name", "store__code"]
#     list_filter = ["created_at", "role", "is_default"]
#
#
# admin.site.register(StoreUser, StoreUserAdmin)
