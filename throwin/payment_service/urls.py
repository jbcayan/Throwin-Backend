from django.urls import path
from .views import (
    PaymentHistoryView,
    StaffDisbursementRequestView,
    AdminDisbursementRequestView,
    StaffBalanceView,
    AdminBalanceView,
)

urlpatterns = [
    # Payment History Endpoints
    path(
        'payments/',
        PaymentHistoryView.as_view(),
        name='payment-history'  # Allows customers and staff to manage payments
    ),

    # Staff Disbursement Endpoints
    path(
        'staff/disbursements/',
        StaffDisbursementRequestView.as_view(),
        name='staff-disbursement-list-create'  # Allows staff to view and create disbursement requests
    ),

    # Admin Disbursement Management Endpoints
    path(
        'admin/disbursements/<int:pk>/',
        AdminDisbursementRequestView.as_view(),
        name='admin-disbursement-manage'  # Allows admins to update disbursement statuses
    ),
    path(
        'admin/disbursements/',
        AdminDisbursementRequestView.as_view(),
        name='admin-disbursement-list'  # Allows admins to list all disbursement requests
    ),

    # Staff Balance Endpoints
    path(
        'staff/balance/',
        StaffBalanceView.as_view(),
        name='staff-balance'  # Allows staff to view their balance
    ),

    # Admin Balance Endpoints
    path(
        'admin/balances/',
        AdminBalanceView.as_view(),
        name='admin-balances'  # Allows admins to view all balances
    ),
]
