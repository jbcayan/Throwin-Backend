from rest_framework import generics, permissions, pagination, status, serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from .models import PaymentHistory
from .serializers import (
    MakePaymentSerializer,
    PaymentHistorySerializer,
    StaffPaymentHistorySerializer,
    AdminPaymentHistorySerializer,
    ConsumerPaymentHistorySerializer,
    RestaurantOwnerPaymentHistorySerializer,
)
from .filters import PaymentHistoryFilter
from .helpers.paypal_helper import create_paypal_payment, execute_paypal_payment
from accounts.choices import UserKind
import logging

# Initialize logger
logger = logging.getLogger(__name__)


class StandardResultsPagination(pagination.PageNumberPagination):
    """
    Custom pagination class for consistent paginated responses.
    """
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


@extend_schema(
    request=MakePaymentSerializer,
    responses={
        201: OpenApiResponse(
            description="Payment creation response with approval URL.",
            examples={
                "nickname": "JohnDoe",
                "amount": "50.00",
                "currency": "USD",
                "payment_method": "paypal",
                "approval_url": "https://www.sandbox.paypal.com/...",
            },
        )
    },
)
class MakePaymentView(generics.CreateAPIView):
    """
    Create a payment and generate a PayPal approval URL.
    """
    serializer_class = MakePaymentSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        logger.info(f"Incoming payload: {request.data}")
        return_url = request.data.get("return_url")
        cancel_url = request.data.get("cancel_url")

        if not return_url or not cancel_url:
            raise serializers.ValidationError({"error": "Both return_url and cancel_url are required."})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = serializer.save()

        paypal_response = create_paypal_payment(
            amount=float(payment.amount),
            currency=payment.currency,
            description=f"Payment to {payment.staff.username}",
            return_url=return_url,
            cancel_url=cancel_url,
        )

        if paypal_response.get("success"):
            paypal_payment = paypal_response["payment"]
            payment_details = paypal_payment.to_dict()

            payment.transaction_id = payment_details.get("id")
            payment.save()

            approval_url = next(
                (link.get("href") for link in payment_details.get("links", []) if link.get("rel") == "approval_url"),
                None
            )

            if approval_url:
                response_data = {
                    "nickname": payment.nickname,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "payment_method": payment.payment_method,
                    "approval_url": approval_url,
                }
                logger.info(f"Response being sent: {response_data}")
                return Response(response_data, status=status.HTTP_201_CREATED)

            raise serializers.ValidationError({"error": "Approval URL not found in PayPal response."})

        error_message = paypal_response.get("error", "Failed to process payment with PayPal.")
        raise serializers.ValidationError({"error": error_message})


@extend_schema(
    parameters=[
        OpenApiParameter("search", str, description="Search across relevant fields."),
        OpenApiParameter("ordering", str, description="Order by payment date or amount."),
    ]
)
class RoleBasedPaymentHistoryView(generics.ListAPIView):
    """
    List payment history based on user roles.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PaymentHistoryFilter
    search_fields = ["transaction_id", "staff__name", "customer__username", "nickname"]
    ordering_fields = ["payment_date", "amount"]
    pagination_class = StandardResultsPagination

    def get_serializer_class(self):
        """
        Return serializer class based on the user's role.
        """
        user = self.request.user
        if user.kind == UserKind.RESTAURANT_STAFF:
            return StaffPaymentHistorySerializer
        elif user.kind == UserKind.CONSUMER:
            return ConsumerPaymentHistorySerializer
        elif user.kind == UserKind.RESTAURANT_OWNER:
            return RestaurantOwnerPaymentHistorySerializer
        elif user.kind == UserKind.SALES_AGENT:
            return AdminPaymentHistorySerializer  # Provides visibility for sales agents.
        elif user.kind in [UserKind.SUPER_ADMIN, UserKind.FC_ADMIN, UserKind.GLOW_ADMIN]:
            return AdminPaymentHistorySerializer
        raise AssertionError("No serializer defined for this role.")

    def get_queryset(self):
        """
        Filter queryset based on the user's role.
        """
        user = self.request.user
        queryset = PaymentHistory.objects.all()

        if user.kind == UserKind.RESTAURANT_STAFF:
            queryset = queryset.filter(staff=user)
        elif user.kind == UserKind.CONSUMER:
            queryset = queryset.filter(customer=user)
        elif user.kind == UserKind.RESTAURANT_OWNER:
            queryset = queryset.filter(restaurant__restaurant_owner=user)
        elif user.kind == UserKind.SALES_AGENT:
            queryset = queryset.filter(restaurant__sales_agent=user)

        # Optimize database queries with related fields
        return queryset.select_related("staff", "restaurant", "store", "customer")


@extend_schema(
    parameters=[
        OpenApiParameter("paymentId", str, required=True, description="PayPal payment ID."),
        OpenApiParameter("PayerID", str, required=True, description="PayPal Payer ID."),
    ],
    responses={
        200: OpenApiResponse(description="Payment completed successfully."),
        400: OpenApiResponse(description="Missing paymentId or PayerID, or PayPal execution failed."),
        404: OpenApiResponse(description="Payment not found."),
    },
)
class PayPalSuccessView(APIView):
    """
    Handle PayPal success callback.
    """
    def get(self, request):
        payment_id = request.GET.get("paymentId")
        payer_id = request.GET.get("PayerID")

        if not payment_id or not payer_id:
            return Response({"error": "Missing paymentId or PayerID"}, status=status.HTTP_400_BAD_REQUEST)

        paypal_response = execute_paypal_payment(payment_id, payer_id)

        if paypal_response["success"]:
            try:
                payment = PaymentHistory.objects.get(transaction_id=payment_id)
                payment.status = "success"
                payment.save()
                return Response({"message": "Payment completed successfully."}, status=status.HTTP_200_OK)
            except PaymentHistory.DoesNotExist:
                return Response({"error": "Payment not found in the system."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"error": paypal_response["error"]}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    parameters=[
        OpenApiParameter("paymentId", str, required=False, description="PayPal payment ID."),
    ],
    responses={200: OpenApiResponse(description="Payment was canceled.")},
)
class PayPalCancelView(APIView):
    """
    Handle PayPal cancel callback.
    """
    def get(self, request):
        payment_id = request.GET.get("paymentId")
        if payment_id:
            try:
                payment = PaymentHistory.objects.get(transaction_id=payment_id)
                payment.status = "canceled"
                payment.save()
            except PaymentHistory.DoesNotExist:
                pass  # No action needed if payment record is not found
        return Response({"message": "Payment was canceled."}, status=status.HTTP_200_OK)



from .serializers import StaffRecentMessagesSerializer
from rest_framework import status, permissions
from accounts.models import User

class StaffRecentMessagesView(APIView):
    permission_classes = [permissions.AllowAny]
    """
    API to fetch the last 5 messages for a staff's transactions with non-empty messages based on their UID.
    """
    def get(self, request, uid):
        try:
            # Fetch the staff user with the given UID
            staff = User.objects.get(uid=uid, kind=UserKind.RESTAURANT_STAFF)

            # Fetch the last 5 transactions with non-empty messages for the staff
            recent_transactions = PaymentHistory.objects.filter(
                staff=staff, message__isnull=False
            ).exclude(
                message__exact=""
            ).order_by('-payment_date')[:5]

            # Serialize the transaction data
            serializer = StaffRecentMessagesSerializer(recent_transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {"error": "Staff not found or not authorized."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )