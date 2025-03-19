import logging

from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, pagination, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.choices import UserKind
from gacha.models import SpinBalance
from store.models import Store
from .models import GMOCreditPayment
from .serializers import GMOCreditPaymentSerializer

User = get_user_model()

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
            # Check payment status with GMO API
            status_response = payment.check_payment_status()

            # Proceed only if payment status is "CAPTURE" (successful)
            if status_response and payment.status == "CAPTURE":
                try:
                    # Use a string literal for the type annotation to avoid Pylance errors
                    staff: "User" = User.objects.get(uid=payment.staff_uid)
                except User.DoesNotExist:
                    logger.error("Staff user with uid %s not found", payment.staff_uid)
                    return Response({"error": "Staff user not found"}, status=status.HTTP_404_NOT_FOUND)
                
                staff_profile = staff.profile
                staff_profile.total_score += int(payment.amount)
                staff_profile.save(update_fields=['total_score'])

                if payment.customer:
                    try:
                        store = Store.objects.get(uid=payment.store_uid)
                    except Store.DoesNotExist:
                        logger.error("Store with uid %s not found", payment.store_uid)
                        return Response({"error": "Store not found"}, status=status.HTTP_404_NOT_FOUND)
                    spin_balance, created = SpinBalance.objects.get_or_create(
                        consumer=payment.customer,
                        store=store,
                        restaurant=store.restaurant
                    )
                    spin_balance.refresh_from_db(fields=['total_spend'])
                    spin_balance.total_spend += payment.amount
                    spin_balance.save()

                # Distribute the net payment to Staff, Glow Admin, FC Admin, and Sales Agent.
                # Note: The distribute_payment() method itself includes a guard for payment status.
                payment.distribute_payment()

            return Response(GMOCreditPaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
        else:
            logger.error("Payment processing failed: %s", serializer.errors)
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
            restaurant = user.get_restaurant_owner_restaurant
            if restaurant:
                queryset = queryset.filter(store_uid__in=[store.uid for store in restaurant.stores.all()])
            else:
                queryset = GMOCreditPayment.objects.none()  # No access if no linked restaurant
        elif user.kind == UserKind.SALES_AGENT:
            agent_restaurants = user.get_agent_restaurants or []
            store_uids = [store.uid for restaurant in agent_restaurants for store in restaurant.stores.all()]
            queryset = queryset.filter(store_uid__in=store_uids)
        elif user.kind not in [UserKind.SUPER_ADMIN, UserKind.FC_ADMIN, UserKind.GLOW_ADMIN]:
            queryset = GMOCreditPayment.objects.none()  # Deny access if unauthorized

        # Filtering by detected store, restaurant, or sales agent
        store_uid = self.request.query_params.get("store_uid")
        if store_uid:
            queryset = queryset.filter(store_uid=store_uid)

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
            return Response({
                "order_id": order_id,
                "status": payment.status,
                "transaction_id": payment.transaction_id,
                "approval_code": payment.approval_code,
                "process_date": payment.process_date,
                "amount": payment.amount,
                "currency": payment.currency,
                "card_last4": payment.card_last4,
            }, status=status.HTTP_200_OK)
        except GMOCreditPayment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)
