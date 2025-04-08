from django.contrib import admin

from .models import Review, Reply


# Register your models here.
class ReviewAdmin(admin.ModelAdmin):
    """Admin configuration for Review model."""
    list_display = ["uid", "id", "consumer", "payment_type", "transaction_id", "created_at"]
    search_fields = ["uid", "id", "transaction_id", "created_at"]

admin.site.register(Review, ReviewAdmin)

class ReplyAdmin(admin.ModelAdmin):
    """Admin configuration for Reply model."""
    list_display = ["uid", "id", "consumer", "created_at"]
    search_fields = ["uid", "id", "review__id", "created_at"]

admin.site.register(Reply, ReplyAdmin)
