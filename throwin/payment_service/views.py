from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .models import PaymentHistory, DisbursementRequest, Balance, DisbursementStatus
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
        if view.__class__.__name__ in ['StaffBalanceView', 'AdminBalanceView']:
            return True  # Allow balance views
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
        """
        Override to handle anonymous payments and balance updates.
        """
        user = self.request.user if self.request.user.is_authenticated else None
        staff_uuid = serializer.validated_data.get("staff").uid

        try:
            staff_user = User.objects.get(uid=staff_uuid, kind=UserKind.RESTAURANT_STAFF)
        except User.DoesNotExist:
            raise ValidationError({"staff": "Invalid staff UUID or not a restaurant staff member."})

        if serializer.validated_data.get("anonymous", False):
            nickname = serializer.validated_data.get("user_nick_name", "Anonymous User")
            payment = serializer.save(customer=None, staff=staff_user, user_nick_name=nickname)
        else:
            payment = serializer.save(customer=user, staff=staff_user)

        try:
            balance, _ = Balance.objects.get_or_create(staff=staff_user)
            balance.update_balance(payment)
        except Exception as e:
            raise ValidationError({"error": f"Failed to update balance: {str(e)}"})


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
        """
        Override to ensure balance checks are performed during creation.
        Automatically sets the staff to the authenticated user.
        """
        if self.request.user.kind != UserKind.RESTAURANT_STAFF:
            raise PermissionDenied("Only staff members can create disbursement requests.")
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
        """
        Override to handle balance deduction when a request is marked as completed.
        """
        if 'status' in serializer.validated_data:
            new_status = serializer.validated_data['status']
            disbursement = serializer.instance

            if new_status == DisbursementStatus.COMPLETED and disbursement.status != DisbursementStatus.COMPLETED:
                try:
                    staff_balance = disbursement.staff.balance
                    staff_balance.total_disbursed += disbursement.amount
                    staff_balance.save()
                except AttributeError:
                    raise ValidationError("Staff balance record might be missing.")

            serializer.save(processed_by=self.request.user)
        else:
            raise PermissionDenied("Only the status can be updated by an admin.")


from rest_framework.exceptions import NotFound
import logging
logger = logging.getLogger(__name__)
from rest_framework.generics import get_object_or_404
from django.http import Http404
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework import status

class StaffBalanceView(generics.RetrieveAPIView):
    """
    View for staff to retrieve their balance.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Ensure the user is a staff member
            staff = request.user
            if staff.kind != UserKind.RESTAURANT_STAFF:
                return Response({"detail": "Only staff can view their balance."}, status=status.HTTP_403_FORBIDDEN)

            print(f"Debug: Attempting to fetch balance for staff user with ID {staff.id}")

            # Explicitly fetch the balance record
            balance = get_object_or_404(Balance, staff=staff)

            print(f"Debug: Balance record found for staff user with ID {staff.id}")

            # Return the balance data
            return Response({
                "total_earned": balance.total_earned,
                "total_disbursed": balance.total_disbursed,
                "management_balance": balance.management_balance,
            })

        except Http404:
            print(f"Warning: Balance record not found for staff user with ID {request.user.id}")
            raise NotFound("Balance record not found for this staff member.")
        except Exception as e:
            print(f"Error: Unexpected error while retrieving balance for staff user with ID {request.user.id}: {e}")
            return Response({"error": "Unable to retrieve balance."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class AdminBalanceView(generics.ListAPIView):
    """
    View for admins to retrieve all balances.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("Only admins can view all balances.")

        balances = Balance.objects.select_related('staff')
        return Response({
            "balances": [
                {
                    "staff": balance.staff.name,
                    "total_earned": balance.total_earned,
                    "total_disbursed": balance.total_disbursed,
                    "management_balance": balance.management_balance,
                }
                for balance in balances
            ]
        })
