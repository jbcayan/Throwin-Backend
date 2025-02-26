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



from django.contrib import admin
from payment_service.bank_details.bank_details_model import BankAccount


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "user", "bank_name", "account_number", "account_type", "is_active", "created_at"
    )
    search_fields = ("user__email", "bank_name", "account_number")
    list_filter = ("bank_name", "account_type", "is_active")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        """Ensure superusers see all, but regular admins see limited data."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def deactivate_others(self, obj):
        """Ensure only one bank account is active per user."""
        if obj.is_active:
            BankAccount.objects.filter(user=obj.user).exclude(id=obj.id).update(is_active=False)

    def save_model(self, request, obj, form, change):
        """Enforce single active bank account when saving from admin."""
        self.deactivate_others(obj)
        super().save_model(request, obj, form, change)




from django.contrib import admin
from .gmo_pg.models import GMOCreditPayment

@admin.register(GMOCreditPayment)
class GMOCreditPaymentAdmin(admin.ModelAdmin):
    """
    Admin panel configuration for GMOCreditPayment.
    """
    list_display = (
        "order_id", "nickname", "amount", "currency", "status",
        "transaction_id", "approval_code", "process_date", "created_at"
    )
    list_filter = ("status", "created_at")
    search_fields = ("order_id", "transaction_id", "nickname", "staff_uid")
    ordering = ("-created_at",)
    readonly_fields = (
        "order_id", "customer", "nickname", "staff_uid", "store_uid", 
        "amount", "currency", "status", "transaction_id", "approval_code",
        "process_date", "card_last4", "expire_date", "pay_method",
        "forward", "created_at", "updated_at"
    )

    fieldsets = (
        ("Transaction Details", {
            "fields": (
                "order_id", "customer", "nickname", "staff_uid", "store_uid",
                "amount", "currency", "status", "transaction_id", "approval_code",
                "process_date"
            )
        }),
        ("Card Details", {
            "fields": ("card_last4", "expire_date", "pay_method", "forward"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of GMO Payments from Admin Panel."""
        return False  # Payments should only be created through API calls

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of payments from the Admin Panel."""
        return False  # Payments should not be deleted for audit trail purposes
