from django.contrib import admin
from .models import PaymentHistory


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    """
    Enhanced Admin interface for PaymentHistory model.
    """
    list_display = (
        "transaction_id",
        "customer_display",
        "nickname",
        "staff_display",
        "restaurant",
        "store_display",
        "amount",
        "currency",
        "service_fee",
        "net_amount",
        "status",
        "payment_method",
        "is_distributed",
        "payment_date",
    )
    list_filter = (
        "status",
        "currency",
        "payment_method",
        "restaurant",
        "store",
        "is_distributed",
        "payment_date",
    )
    search_fields = (
        "transaction_id",
        "customer__username",
        "customer__email",
        "nickname",
        "staff__name",
        "staff__email",
        "restaurant__name",
        "store__name",
    )
    readonly_fields = (
        "transaction_id",
        "service_fee",
        "net_amount",
        "payment_date",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        ("Transaction Details", {
            "fields": (
                "transaction_id",
                "customer",
                "nickname",
                "staff",
                "restaurant",
                "store",
                "amount",
                "currency",
                "status",
                "message",
                "payment_method",
                "is_distributed",
            )
        }),
        ("Financial Details", {
            "fields": (
                "service_fee",
                "net_amount",
            )
        }),
        ("Timestamps", {
            "fields": ("payment_date", "created_at", "updated_at")
        }),
    )
    ordering = ("-payment_date",)
    list_per_page = 20
    date_hierarchy = "payment_date"

    def customer_display(self, obj):
        """
        Display customer details in a user-friendly format.
        """
        return obj.customer.username if obj.customer else "Anonymous"
    customer_display.short_description = "Customer"

    def staff_display(self, obj):
        """
        Display staff details in a user-friendly format.
        """
        return obj.staff.name
    staff_display.short_description = "Staff"

    def store_display(self, obj):
        """
        Display store details in a user-friendly format.
        """
        return obj.store.name if obj.store else "N/A"
    store_display.short_description = "Store"

    def get_queryset(self, request):
        """
        Optimize queryset for admin by prefetching related objects.
        """
        return super().get_queryset(request).select_related(
            "customer", "staff", "restaurant", "store"
        )
