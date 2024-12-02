from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import PaymentHistory, DisbursementRequest
from .serializers import PaymentHistorySerializer, DisbursementRequestSerializer
from accounts.choices import UserKind
from accounts.models import User


class StandardResultsPagination(PageNumberPagination):
    """
    Custom pagination class for standardized results with configurable page size.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsStaffOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow access only to staff or admin users.
    """
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
    View for managing payment histories:
    - Any user can create a payment (authenticated or anonymous).
    - Authenticated users can view their payment history.
    - Staff can view payments received by them.
    - Admins can view all payment histories.
    """
    serializer_class = PaymentHistorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['staff', 'status']
    ordering_fields = ['created_at', 'amount']
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return PaymentHistory.objects.all()
        if user.kind == UserKind.CONSUMER:
            return PaymentHistory.objects.filter(customer=user)
        if user.kind == UserKind.RESTAURANT_STAFF:
            return PaymentHistory.objects.filter(staff=user)
        return PaymentHistory.objects.none()

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        staff_uuid = serializer.validated_data.get("staff")
        try:
            staff_user = User.objects.get(uid=staff_uuid, kind=UserKind.RESTAURANT_STAFF)
        except User.DoesNotExist:
            raise ValidationError({"staff": "Invalid staff UUID or not a restaurant staff member."})

        if serializer.validated_data.get("anonymous", False):
            nickname = serializer.validated_data.get("user_nick_name", "Anonymous User")
            serializer.save(customer=None, staff=staff_user, user_nick_name=nickname)
        else:
            serializer.save(customer=user, staff=staff_user)


class StaffDisbursementRequestView(generics.ListCreateAPIView):
    """
    View for managing disbursement requests for staff:
    - Staff can view their disbursement requests.
    - Staff can create new disbursement requests.
    """
    serializer_class = DisbursementRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrAdmin]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        return DisbursementRequest.objects.filter(staff=self.request.user).select_related('processed_by')

    def perform_create(self, serializer):
        serializer.save(staff=self.request.user)


class AdminDisbursementRequestView(generics.ListAPIView, generics.UpdateAPIView):
    """
    View for managing disbursement requests for admins:
    - Admins can view all disbursement requests.
    - Admins can update the status of requests.
    """
    queryset = DisbursementRequest.objects.select_related('staff', 'processed_by')
    serializer_class = DisbursementRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'staff']
    ordering_fields = ['created_at', 'amount']
    pagination_class = StandardResultsPagination
    lookup_field = 'pk'

    def perform_update(self, serializer):
        if 'status' in serializer.validated_data:
            serializer.save(processed_by=self.request.user)
        else:
            raise PermissionDenied("Only the status can be updated by an admin.")
