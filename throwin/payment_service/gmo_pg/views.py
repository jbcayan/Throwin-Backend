import logging
from rest_framework import generics, permissions, pagination, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.choices import UserKind
from .models import GMOCreditPayment
from .serializers import GMOCreditPaymentSerializer

# Initialize logger
logger = logging.getLogger(__name__)

class StandardResultsPagination(pagination.PageNumberPagination):
    """Custom pagination class for consistent paginated responses."""
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

# ------------------------------------
# ✅ 1. API to Create & Process Payment
# ------------------------------------
class GMOCreditCardPaymentView(generics.CreateAPIView):
    """
    API to process GMO PG credit card payment.
    Endpoint: `/gmo-pg/credit-card/`
    """
    serializer_class = GMOCreditPaymentSerializer
    permission_classes = [permissions.AllowAny]  # Supports anonymous payments

    def create(self, request, *args, **kwargs):
        logger.info(f"Received payment request: {request.data}")

        serializer = self.get_serializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            payment = serializer.save()
            return Response(GMOCreditPaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

        logger.error(f"Payment processing failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --------------------------------------------------
# ✅ 2. Role-Based API to Retrieve Payment History
# --------------------------------------------------
class RoleBasedPaymentHistoryView(generics.ListAPIView):
    """
    API to retrieve payment history based on user role.
    - **Staff** can view only payments they received.
    - **Customers** can view only their own payments.
    - **Restaurant Owners** can view payments of their restaurants.
    - **Sales Agents** can view payments related to their managed businesses.
    - **Admins** can view all payments.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GMOCreditPaymentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["transaction_id", "staff_uid", "nickname", "customer__username"]
    ordering_fields = ["created_at", "amount"]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        user = self.request.user
        queryset = GMOCreditPayment.objects.all()

        if user.kind == UserKind.RESTAURANT_STAFF:
            queryset = queryset.filter(staff_uid=user.uid)  # Only their received payments
        elif user.kind == UserKind.CONSUMER:
            queryset = queryset.filter(customer=user)  # Only their own payments
        elif user.kind == UserKind.RESTAURANT_OWNER:
            queryset = queryset.filter(restaurant_uid__in=user.get_agent_restaurants or [])
        elif user.kind == UserKind.SALES_AGENT:
            queryset = queryset.filter(sales_agent_uid=user.uid)
        elif user.kind not in [UserKind.SUPER_ADMIN, UserKind.FC_ADMIN, UserKind.GLOW_ADMIN]:
            queryset = GMOCreditPayment.objects.none()  # Deny access if unauthorized

        return queryset

# --------------------------------------------
# ✅ 3. API to Check Payment Status
# --------------------------------------------
class CheckGMOPaymentStatusView(APIView):
    """
    API to check the status of a specific payment.
    Endpoint: `/gmo-pg/payment-status/{order_id}/`
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        try:
            payment = GMOCreditPayment.objects.get(order_id=order_id)
            return Response({"order_id": order_id, "status": payment.status}, status=status.HTTP_200_OK)
        except GMOCreditPayment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)
