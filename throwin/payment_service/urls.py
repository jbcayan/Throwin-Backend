from django.urls import path
from .views import (
    PaymentHistoryView,
    StaffDisbursementRequestView,
    AdminDisbursementRequestView,
)

urlpatterns = [
    # Payment History Endpoint
    path(
        'payments/',
        PaymentHistoryView.as_view(),
        name='payment-history'
    ),

    # Disbursement Endpoints for Staff (List and Create)
    path(
        'staff/disbursements/',
        StaffDisbursementRequestView.as_view(),
        name='staff-disbursement-list-create'
    ),

    # Disbursement Management Endpoint for Admin
    path(
        'admin/disbursements/<int:pk>/',
        AdminDisbursementRequestView.as_view(),
        name='admin-disbursement-manage'
    ),

    # Disbursement List Endpoint for Admin
    path(
        'admin/disbursements/',
        AdminDisbursementRequestView.as_view(),
        name='admin-disbursement-list'
    ),
]
