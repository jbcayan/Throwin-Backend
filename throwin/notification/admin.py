from django.contrib import admin
from notification.models import Notification


# Register your models here.
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "uid",
        "id",
        "title",
        "body",
        "created_at",
    )


admin.site.register(Notification, NotificationAdmin)
