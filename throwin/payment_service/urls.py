from django.urls import path
from .views import (
    MakePaymentView,
    PayPalSuccessView,
    PayPalCancelView,
    RoleBasedPaymentHistoryView,
    StaffRecentMessagesView,
    UserBankAccountListCreateView,
    UserBankAccountUpdateView

)


from .dashboard_stats import PaymentStatsView


from .gmo_pg.views import (
    GMOCreditCardPaymentView,
    RoleBasedPaymentHistoryView,
    CheckGMOPaymentStatusView
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


    # Endppoint for Bank Details
    path("bank-accounts/", UserBankAccountListCreateView.as_view(), name="user-bank-accounts"),
    path("bank-accounts/<int:pk>/", UserBankAccountUpdateView.as_view(), name="user-bank-account-detail"),

    ### GMO PG Credit Card Payment

    # Process a new credit card payment
    path("gmo-pg/credit-card/", GMOCreditCardPaymentView.as_view(), name="gmo_credit_card_payment"),
    # Get payment history based on user roles
    path("gmo-pg/credit-card/payment-history/", RoleBasedPaymentHistoryView.as_view(), name="gmo_payment_history"),
    # # Check payment status
    # path("gmo-pg/credit-card/payment-status/<str:order_id>/", CheckGMOPaymentStatusView.as_view(), name="gmo_payment_status"),


    
    path("analytics/stats/", PaymentStatsView.as_view(), name="payment_stats"),
]
