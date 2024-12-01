from django.urls import path
from .views import PaymentHistoryView, StaffDisbursementRequestView, AdminDisbursementRequestView

urlpatterns = [
    # Payment History Endpoint
    path('payments/', PaymentHistoryView.as_view(), name='payment-history'),

    # Disbursement Endpoints for Staff (List and Create)
    path('disbursements/', StaffDisbursementRequestView.as_view(), name='staff-disbursement-list-create'),
    
    # Disbursement Management Endpoint for Admin (Retrieve and Update by UUID)
    path('disbursements/<uuid:id>/', AdminDisbursementRequestView.as_view(), name='admin-disbursement-manage'),
]
