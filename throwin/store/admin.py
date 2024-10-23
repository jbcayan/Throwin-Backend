from django.contrib import admin
from store.models import Store


# Register your models here.
class StoreAdmin(admin.ModelAdmin):
    list_display = ["id", "uid", "name", "code", "created_at"]
    search_fields = ["name", "code"]
    list_filter = ["created_at"]


admin.site.register(Store, StoreAdmin)
