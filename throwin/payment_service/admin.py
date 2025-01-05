from django.contrib import admin
from .models import PaymentHistory

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "customer",
        "nickname",
        "staff",
        "amount",
        "currency",
        "status",
        "is_distributed",
        "payment_date",
        "payment_method",
        "service_fee",
        "net_amount",
    )
    list_filter = (
        "status",
        "is_distributed",
        "payment_method",
        "currency",
        "payment_date",
    )
    search_fields = (
        "transaction_id",
        "customer__name",
        "customer__email",
        "nickname",
        "staff__name",
        "staff__email",
    )
    ordering = ("-payment_date",)
    readonly_fields = (
        "transaction_id",
        "customer",
        "staff",
        "amount",
        "currency",
        "payment_date",
        "payment_method",
        "service_fee",
        "net_amount",
    )
    fieldsets = (
        (
            "Payment Details",
            {
                "fields": (
                    "transaction_id",
                    "customer",
                    "nickname",
                    "staff",
                    "amount",
                    "currency",
                    "payment_date",
                )
            },
        ),
        (
            "Payment Status",
            {
                "fields": (
                    "status",
                    "is_distributed",
                )
            },
        ),
        (
            "Additional Details",
            {
                "fields": (
                    "payment_method",
                    "service_fee",
                    "net_amount",
                )
            },
        ),
    )
