from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from .models import PaymentHistory, DisbursementRequest
from .serializers import PaymentHistorySerializer, DisbursementRequestSerializer
from accounts.choices import UserKind

class StandardResultsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class IsStaffOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if view.__class__.__name__ == 'StaffDisbursementRequestView' and user.kind == UserKind.RESTAURANT_STAFF:
            return True
        if view.__class__.__name__ == 'AdminDisbursementRequestView' and user.is_superuser:
            return True
        return False

class PaymentHistoryView(generics.ListCreateAPIView):
    """
    Allows any user to create a payment (authenticated or anonymous).
    Authenticated users can view their payment history.
    """
    serializer_class = PaymentHistorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['staff__id', 'status', 'customer__id']  # Updated for UUIDs
    ordering_fields = ['created_at', 'amount']
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.kind == UserKind.CONSUMER:
                return PaymentHistory.objects.filter(customer__id=user.id)
            elif user.kind == UserKind.RESTAURANT_STAFF:
                return PaymentHistory.objects.filter(staff__id=user.id)
        return PaymentHistory.objects.none()

    def perform_create(self, serializer):
        customer = self.request.user if self.request.user.is_authenticated and not serializer.validated_data.get("anonymous") else None
        serializer.save(customer=customer)

class StaffDisbursementRequestView(generics.ListCreateAPIView):
    serializer_class = DisbursementRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrAdmin]

    def get_queryset(self):
        return DisbursementRequest.objects.filter(staff__id=self.request.user.id).select_related('processed_by')

    def perform_create(self, serializer):
        # Automatically set the staff field to the authenticated user's UUID
        serializer.save(staff=self.request.user)

class AdminDisbursementRequestView(generics.ListAPIView, generics.RetrieveUpdateAPIView):
    """
    Allows admin users to view all disbursement requests and update their status.
    """
    queryset = DisbursementRequest.objects.select_related('staff', 'processed_by')
    serializer_class = DisbursementRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrAdmin]
    lookup_field = 'id'  # Use UUID instead of the default `pk`

    def perform_update(self, serializer):
        # Only allow admin to update the status and set processed_by field
        if 'status' in serializer.validated_data:
            serializer.save(processed_by=self.request.user)
        else:
            raise PermissionDenied("Only the status can be updated by an admin.")
