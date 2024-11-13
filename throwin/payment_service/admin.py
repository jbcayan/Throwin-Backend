from django.contrib import admin
from .models import PaymentHistory, DisbursementRequest

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'customer', 'staff', 'amount', 'status',
        'payment_method', 'anonymous', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'anonymous', 'created_at')
    search_fields = ('transaction_id', 'customer__username', 'staff__username', 'customer_email', 'customer_phone')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('customer', 'staff')

@admin.register(DisbursementRequest)
class DisbursementRequestAdmin(admin.ModelAdmin):
    list_display = ('staff', 'amount', 'status', 'processed_by', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('staff__username', 'processed_by__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('staff', 'processed_by')
