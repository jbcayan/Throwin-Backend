from django.contrib import admin
from .models import PaymentHistory, DisbursementRequest, Balance


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the PaymentHistory model.
    """
    list_display = (
        'transaction_id', 'customer', 'staff', 'amount', 'status',
        'anonymous', 'payment_method', 'created_at'
    )
    list_filter = ('status', 'anonymous', 'payment_method', 'created_at')
    search_fields = ('transaction_id', 'customer__username', 'staff__username', 'user_nick_name')
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


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Balance model.
    """
    list_display = (
        'staff', 'total_earned', 'total_disbursed', 'management_balance',
        'glow_share', 'sales_agency_share', 'franchise_share', 'created_at'
    )
    list_filter = ('created_at',)
    search_fields = ('staff__username', 'staff__email')
    readonly_fields = (
        'total_earned', 'total_disbursed', 'management_balance',
        'glow_share', 'sales_agency_share', 'franchise_share', 'created_at', 'updated_at'
    )
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': (
                'staff', 'total_earned', 'total_disbursed', 'management_balance',
                'glow_share', 'sales_agency_share', 'franchise_share'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(DisbursementRequest)
class DisbursementRequestAdmin(admin.ModelAdmin):
    """
    Admin configuration for the DisbursementRequest model.
    """
    list_display = ('staff', 'amount', 'status', 'processed_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('staff__username', 'processed_by__username', 'staff__email')
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
