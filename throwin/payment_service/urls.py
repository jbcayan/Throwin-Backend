from django.urls import path
from .views import (
    MakePaymentView,
    PayPalSuccessView,
    PayPalCancelView,
    CustomerPaymentHistoryView,
    StaffPaymentHistoryView,
    AdminPaymentHistoryView,
)

urlpatterns = [
    path("make-payment/", MakePaymentView.as_view(), name="make_payment"),

    path("paypal-success/", PayPalSuccessView.as_view(), name="paypal_success"),
    path("paypal-cancel/", PayPalCancelView.as_view(), name="paypal_cancel"),
    
    path("customer-payments/", CustomerPaymentHistoryView.as_view(), name="customer_payments"),
    path("staff-payments/", StaffPaymentHistoryView.as_view(), name="staff_payments"),
    path("admin-payments/", AdminPaymentHistoryView.as_view(), name="admin_payments"),
]
