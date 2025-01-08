from django_filters import rest_framework as filters
from .models import PaymentHistory


class PaymentHistoryFilter(filters.FilterSet):
    """
    FilterSet for filtering payment histories based on various fields.
    """
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
        help_text="Search by staff name (case-insensitive)"
    )
    customer_name = filters.CharFilter(
        field_name="customer__username",
        lookup_expr="icontains",
        help_text="Search by customer username (case-insensitive)"
    )
    restaurant_name = filters.CharFilter(
        field_name="restaurant__name",
        lookup_expr="icontains",
        help_text="Search by restaurant name (case-insensitive)"
    )
    store_name = filters.CharFilter(
        field_name="store__name",
        lookup_expr="icontains",
        help_text="Search by store name (case-insensitive)"
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
    transaction_id = filters.CharFilter(
        field_name="transaction_id",
        lookup_expr="icontains",
        help_text="Search by transaction ID (case-insensitive)"
    )

    class Meta:
        model = PaymentHistory
        fields = [
            "status",
            "payment_date",
            "amount",
            "staff_name",
            "customer_name",
            "restaurant_name",
            "store_name",
            "currency",
            "payment_method",
            "transaction_id",
        ]
