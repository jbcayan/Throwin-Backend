from django.urls import path
from .views import (
    MakePaymentView,
    PayPalSuccessView,
    PayPalCancelView,
    RoleBasedPaymentHistoryView,
    StaffRecentMessagesView
)

# Namespace for the app
app_name = "payment_service"

urlpatterns = [
    # Endpoint to create a payment
    path("make-payment/", MakePaymentView.as_view(), name="make_payment"),
    
    # PayPal integration callback URLs
    path("paypal-success/", PayPalSuccessView.as_view(), name="paypal_success"),
    path("paypal-cancel/", PayPalCancelView.as_view(), name="paypal_cancel"),
    
    # Endpoint to fetch payment histories based on user roles
    path("payment-histories/", RoleBasedPaymentHistoryView.as_view(), name="payment_histories"),
    
    # Endppoint to get last 5 messgaes for staff
    path('staff/<uuid:uid>/recent-messages/', StaffRecentMessagesView.as_view(), name='staff-recent-messages'),
]