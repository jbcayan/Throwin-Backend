from django_filters import rest_framework as filters
from .models import PaymentHistory

class PaymentHistoryFilter(filters.FilterSet):
    status = filters.CharFilter(
        field_name="status", 
        lookup_expr="iexact",
        help_text="Filter by status (e.g., pending, success, failed, canceled)"
    )
    payment_date = filters.DateFromToRangeFilter(
        field_name="payment_date",
        help_text="Filter payments by a date range (start and end dates)"
    )
    amount = filters.RangeFilter(
        field_name="amount",
        help_text="Filter payments by a range of amounts (min and max)"
    )
    staff_name = filters.CharFilter(
        field_name="staff__name",
        lookup_expr="icontains",
        help_text="Search by staff name"
    )
    customer_name = filters.CharFilter(
        field_name="customer__name",
        lookup_expr="icontains",
        help_text="Search by customer name"
    )
    currency = filters.CharFilter(
        field_name="currency",
        lookup_expr="iexact",
        help_text="Filter by currency (e.g., JPY, USD)"
    )
    payment_method = filters.CharFilter(
        field_name="payment_method",
        lookup_expr="iexact",
        help_text="Filter by payment method (e.g., PayPal, Stripe, Cash)"
    )

    class Meta:
        model = PaymentHistory
        fields = [
            "status",
            "payment_date",
            "amount",
            "staff_name",
            "customer_name",
            "currency",
            "payment_method",
        ]
