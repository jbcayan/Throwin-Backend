from django.contrib import admin
from .models import PaymentHistory, DisbursementRequest


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for PaymentHistory model.
    """
    list_display = (
        'transaction_id', 'customer', 'staff', 'amount', 'status', 
        'anonymous', 'created_at'
    )
    list_filter = ('status', 'anonymous', 'created_at')
    search_fields = ('transaction_id', 'customer__email', 'staff__email', 'user_nick_name')
    ordering = ('-created_at',)
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': (
                'transaction_id', 'customer', 'staff', 'amount', 'status', 
                'anonymous', 'payment_method', 'user_nick_name', 
                'customer_email', 'customer_username', 'customer_phone'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(DisbursementRequest)
class DisbursementRequestAdmin(admin.ModelAdmin):
    """
    Admin configuration for DisbursementRequest model.
    """
    list_display = ('staff', 'amount', 'status', 'processed_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('staff__email', 'processed_by__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('staff', 'amount', 'status', 'processed_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
