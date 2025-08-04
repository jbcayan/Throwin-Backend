# payment_service/dashboard_stats.py

import logging
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers

from common.permissions import (
    CheckAnyPermission,
    IsSuperAdminUser, IsFCAdminUser, IsGlowAdminUser,
    IsSalesAgentUser, IsRestaurantOwnerUser,
)

from .models import GMOCreditPayment, Balance  # <-- updated to GMO + Balance
from store.models import Restaurant, Store
from accounts.choices import UserKind

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import datetime, time
from uuid import UUID

# --- OpenAPI / Swagger (drf-spectacular) ------------------------------------
try:
    from drf_spectacular.utils import (
        extend_schema,
        OpenApiParameter,
        OpenApiTypes,
        OpenApiExample,
    )
except Exception:  # drf-spectacular not installed
    def extend_schema(*args, **kwargs):  # type: ignore
        def _wrap(func):
            return func
        return _wrap

logger = logging.getLogger(__name__)

CAPTURE_STATUS = "CAPTURE"
JPY = "JPY"


# --- Response serializer (for docs) -----------------------------------------
class PaymentTimeseriesItemSerializer(serializers.Serializer):
    date = serializers.DateField(help_text="Day (YYYY-MM-DD)")
    throwin_count = serializers.IntegerField(help_text="Successful payments that day (CAPTURE)")
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, help_text="Sum of gross amounts in JPY for that day"
    )


class PaymentStatsResponseSerializer(serializers.Serializer):
    filters_applied = serializers.DictField(child=serializers.CharField(allow_null=True), help_text="Echo of filters used")
    total_amount_jpy = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Gross total (filtered CAPTURE JPY)")
    total_throwins = serializers.IntegerField(help_text="Number of successful payments (filtered, CAPTURE)")
    latest_balance_jpy = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Current user's Balance.current_balance")
    total_stores = serializers.IntegerField(help_text="Distinct stores (by store_uid) involved in filtered payments")
    timeseries = PaymentTimeseriesItemSerializer(many=True)


# --- Filter logic ------------------------------------------------------------
def _safe_uuid(val: str):
    """Return UUID if valid, else None."""
    try:
        return UUID(val)
    except Exception:
        return None


def _apply_filters(payments_qs, stores_qs, params):
    """
    Apply optional filters to scoped querysets:
      - year: int (e.g., 2025)  -> based on created_at
      - month: int 1-12         -> based on created_at
      - store_uid: UUID (GMOCreditPayment.store_uid)
      - staff_uid: UUID (GMOCreditPayment.staff_uid)
      - date_from, date_to: YYYY-MM-DD (inclusive, on created_at)
    Note: All filters are combined (AND).
    """
    print("[PaymentStats] Applying filters with params:", dict(params))
    year = params.get("year")
    month = params.get("month")
    store_uid = params.get("store_uid")
    staff_uid = params.get("staff_uid")
    date_from = params.get("date_from")
    date_to = params.get("date_to")

    # Year
    if year:
        try:
            y = int(year)
            payments_qs = payments_qs.filter(created_at__year=y)
            print(f"[PaymentStats] Filtered by year={y}")
        except ValueError:
            logger.debug("Ignoring invalid 'year' filter: %r", year)
            print(f"[PaymentStats][WARN] Invalid year filter ignored: {year}")

    # Month
    if month:
        try:
            m = int(month)
            if 1 <= m <= 12:
                payments_qs = payments_qs.filter(created_at__month=m)
                print(f"[PaymentStats] Filtered by month={m}")
            else:
                logger.debug("Ignoring out-of-range 'month': %r", month)
                print(f"[PaymentStats][WARN] Out-of-range month ignored: {month}")
        except ValueError:
            logger.debug("Ignoring invalid 'month' filter: %r", month)
            print(f"[PaymentStats][WARN] Invalid month filter ignored: {month}")

    # Store UID
    if store_uid:
        uid = _safe_uuid(store_uid)
        if uid:
            # narrow stores_qs (used only for debugging/count if needed)
            stores_qs = stores_qs.filter(uid=uid)
            payments_qs = payments_qs.filter(store_uid=uid)
            print(f"[PaymentStats] Filtered by store_uid={uid}")
        else:
            logger.debug("Ignoring invalid 'store_uid' UUID: %r", store_uid)
            print(f"[PaymentStats][WARN] Invalid store_uid ignored: {store_uid}")

    # Staff UID
    if staff_uid:
        uid = _safe_uuid(staff_uid)
        if uid:
            payments_qs = payments_qs.filter(staff_uid=uid)
            print(f"[PaymentStats] Filtered by staff_uid={uid}")
        else:
            logger.debug("Ignoring invalid 'staff_uid' UUID: %r", staff_uid)
            print(f"[PaymentStats][WARN] Invalid staff_uid ignored: {staff_uid}")

    # Date range (inclusive) on created_at
    tz = timezone.get_current_timezone()
    if date_from:
        df = parse_date(date_from)
        if df:
            start_dt = timezone.make_aware(datetime.combine(df, time.min), tz)
            payments_qs = payments_qs.filter(created_at__gte=start_dt)
            print(f"[PaymentStats] Filtered by date_from={start_dt.isoformat()}")
        else:
            logger.debug("Ignoring invalid 'date_from': %r", date_from)
            print(f"[PaymentStats][WARN] Invalid date_from ignored: {date_from}")

    if date_to:
        dt_ = parse_date(date_to)
        if dt_:
            end_dt = timezone.make_aware(datetime.combine(dt_, time.max), tz)
            payments_qs = payments_qs.filter(created_at__lte=end_dt)
            print(f"[PaymentStats] Filtered by date_to={end_dt.isoformat()}")
        else:
            logger.debug("Ignoring invalid 'date_to': %r", date_to)
            print(f"[PaymentStats][WARN] Invalid date_to ignored: {date_to}")

    print(
        "[PaymentStats] After filters -> payments_qs.count():",
        payments_qs.count()
    )
    return payments_qs, stores_qs


def get_role_scoped_qs(user, params=None):
    """
    Returns a dict of querysets scoped to the user's role and filtered by params:
      - payments_qs: GMOCreditPayment filtered by role, CAPTURE status, and JPY (+ filters)
      - stores_qs: Stores visible to the role (used for narrowing scope & debug)
    """
    params = params or {}
    print(f"[PaymentStats] get_role_scoped_qs for user_id={getattr(user, 'id', None)} kind={getattr(user, 'kind', None)}")

    # Base (global) queryset: CAPTURE + JPY
    base_qs = GMOCreditPayment.objects.filter(
        status=CAPTURE_STATUS,
        currency=JPY,
    )

    # Admins see everything
    if user.kind in {UserKind.SUPER_ADMIN, UserKind.FC_ADMIN, UserKind.GLOW_ADMIN}:
        stores_qs = Store.objects.all()
        payments_qs = base_qs
        print("[PaymentStats] Scope=GLOBAL (Admin). Base CAPTURE payments:", payments_qs.count())
        payments_qs, stores_qs = _apply_filters(payments_qs, stores_qs, params)
        return {
            "payments_qs": payments_qs,
            "stores_qs": stores_qs,
        }

    # Sales Agent → restaurants they manage -> stores under those restaurants
    if user.kind == UserKind.SALES_AGENT:
        agent_restaurants = user.get_agent_restaurants or []
        restaurants_qs = Restaurant.objects.filter(pk__in=[r.pk for r in agent_restaurants])
        stores_qs = Store.objects.filter(restaurant__in=restaurants_qs)
        store_uids = list(stores_qs.values_list("uid", flat=True))
        payments_qs = base_qs.filter(store_uid__in=store_uids)
        print("[PaymentStats] Scope=SALES_AGENT. Restaurants:", restaurants_qs.count(), "Stores:", stores_qs.count(), "Base payments:", payments_qs.count())
        payments_qs, stores_qs = _apply_filters(payments_qs, stores_qs, params)
        return {
            "payments_qs": payments_qs,
            "stores_qs": stores_qs,
        }

    # Restaurant Owner → their restaurant(s) -> stores under those restaurants
    if user.kind == UserKind.RESTAURANT_OWNER:
        owned_ids = set()

        single = getattr(user, "get_restaurant_owner_restaurant", None)
        if callable(single):
            r = single()
            if r:
                owned_ids.add(r.pk)

        rel_mgr = getattr(user, "restaurants", None)
        if hasattr(rel_mgr, "values_list"):
            owned_ids.update(rel_mgr.values_list("pk", flat=True))

        restaurants_qs = Restaurant.objects.filter(pk__in=owned_ids)
        stores_qs = Store.objects.filter(restaurant__in=restaurants_qs)
        store_uids = list(stores_qs.values_list("uid", flat=True))
        payments_qs = base_qs.filter(store_uid__in=store_uids)
        print("[PaymentStats] Scope=RESTAURANT_OWNER. Restaurants:", restaurants_qs.count(), "Stores:", stores_qs.count(), "Base payments:", payments_qs.count())
        payments_qs, stores_qs = _apply_filters(payments_qs, stores_qs, params)
        return {
            "payments_qs": payments_qs,
            "stores_qs": stores_qs,
        }

    # Fallback (shouldn’t hit for this endpoint)
    print("[PaymentStats][WARN] Scope fallback hit. User likely unauthorized for this endpoint.")
    return {
        "payments_qs": GMOCreditPayment.objects.none(),
        "stores_qs": Store.objects.none(),
    }


def _get_user_latest_balance(user) -> Decimal:
    """
    Latest balance per request: use Balance model for the **current user only**.
    If the user has no Balance row, return 0.00.
    """
    try:
        bal = Balance.objects.filter(user=user).only("current_balance").first()
        current = bal.current_balance if bal else Decimal("0.00")
        print(f"[PaymentStats] latest_balance_jpy for user_id={getattr(user, 'id', None)} -> {current}")
        return current
    except Exception as e:
        logger.exception("Failed to read Balance for user_id=%s", getattr(user, "id", None))
        print("[PaymentStats][ERROR] Reading Balance failed:", repr(e))
        return Decimal("0.00")


# --- View -------------------------------------------------------------------
class PaymentStatsView(APIView):
    """
    Role-scoped analytics for:
    super_admin, fc_admin, glow_admin, sales_agent, restaurant_owner

    Data source:
      - Payments: GMOCreditPayment (status=CAPTURE, currency=JPY)
      - Latest balance: current authenticated user's Balance.current_balance

    Supported filters (query params):
      - year: int (e.g., 2025)         [created_at]
      - month: int 1-12                [created_at]
      - store_uid: UUID (Store.uid)
      - staff_uid: UUID (User.uid)     [GMOCreditPayment.staff_uid]
      - date_from: YYYY-MM-DD          [created_at, inclusive]
      - date_to: YYYY-MM-DD            [created_at, inclusive]
    """
    permission_classes = [CheckAnyPermission]
    available_permission_classes = [
        IsSuperAdminUser, IsFCAdminUser, IsGlowAdminUser,
        IsSalesAgentUser, IsRestaurantOwnerUser,
    ]

    @extend_schema(
        operation_id="payment_service__payment_stats",
        tags=["Payment Service - Analytics"],
        summary="Get role-scoped payment statistics (GMO + Balance)",
        description=(
            "Returns analytics scoped to the authenticated user's role. "
            "All filters are optional and combined with AND logic. "
            "Payments source: GMOCreditPayment (CAPTURE + JPY). "
            "Latest balance is taken from the current user's Balance.current_balance."
        ),
        parameters=[
            OpenApiParameter(name="year", description="Filter by year (e.g., 2025)", required=False, type=OpenApiTypes.INT),
            OpenApiParameter(name="month", description="Filter by month (1-12)", required=False, type=OpenApiTypes.INT),
            OpenApiParameter(name="store_uid", description="Filter by Store.uid (UUID)", required=False, type=OpenApiTypes.UUID),
            OpenApiParameter(name="staff_uid", description="Filter by User.uid (UUID of staff)", required=False, type=OpenApiTypes.UUID),
            OpenApiParameter(name="date_from", description="Start date inclusive (YYYY-MM-DD)", required=False, type=OpenApiTypes.DATE),
            OpenApiParameter(name="date_to", description="End date inclusive (YYYY-MM-DD)", required=False, type=OpenApiTypes.DATE),
        ],
        responses={200: PaymentStatsResponseSerializer},
        examples=[
            OpenApiExample(
                "Example response",
                value={
                    "filters_applied": {
                        "year": "2025",
                        "month": "7",
                        "store_uid": "5e0f9a7a-8e24-4f55-b6b6-1a6b2f7b2bb1",
                        "staff_uid": None,
                        "date_from": "2025-07-01",
                        "date_to": "2025-07-31",
                    },
                    "total_amount_jpy": "12345.00",
                    "total_throwins": 42,
                    "latest_balance_jpy": "678.00",
                    "total_stores": 3,
                    "timeseries": [
                        {"date": "2025-07-01", "throwin_count": 5, "total_amount": "1500.00"},
                        {"date": "2025-07-02", "throwin_count": 2, "total_amount": "600.00"},
                    ],
                },
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        print("[PaymentStats] GET /analytics/stats called with query_params:", dict(request.query_params))
        try:
            # 1) Build scoped querysets with filters
            scoped = get_role_scoped_qs(request.user, params=request.query_params)
            payments_qs = scoped["payments_qs"]
            print("[PaymentStats] Scoped CAPTURE payments count:", payments_qs.count())

            # 2) Aggregations
            total_amount_jpy = (
                payments_qs.aggregate(total_amount=Sum("amount")).get("total_amount") or Decimal("0.00")
            )
            print("[PaymentStats] total_amount_jpy:", total_amount_jpy)

            total_throwins = payments_qs.count()
            print("[PaymentStats] total_throwins:", total_throwins)

            # Distinct stores involved in filtered payments (by store_uid)
            total_stores = (
                payments_qs.exclude(store_uid__isnull=True)
                .values("store_uid")
                .distinct()
                .count()
            )
            print("[PaymentStats] total_stores (distinct store_uid in payments):", total_stores)

            # Latest balance from Balance model for the current user
            latest_balance = _get_user_latest_balance(request.user)

            # 3) Time series (per day) on created_at
            daily = (
                payments_qs
                .annotate(day=TruncDate("created_at"))
                .values("day")
                .annotate(
                    throwin_count=Count("id"),
                    total_amount=Sum("amount"),
                )
                .order_by("day")
            )
            timeseries = [
                {
                    "date": item["day"],
                    "throwin_count": item["throwin_count"] or 0,
                    "total_amount": item["total_amount"] or Decimal("0.00"),
                }
                for item in daily
            ]
            print("[PaymentStats] timeseries length:", len(timeseries))

            # 4) Build response
            response_data = {
                "filters_applied": {
                    "year": request.query_params.get("year"),
                    "month": request.query_params.get("month"),
                    "store_uid": request.query_params.get("store_uid"),
                    "staff_uid": request.query_params.get("staff_uid"),
                    "date_from": request.query_params.get("date_from"),
                    "date_to": request.query_params.get("date_to"),
                },
                "total_amount_jpy": total_amount_jpy,
                "total_throwins": total_throwins,
                "latest_balance_jpy": latest_balance,
                "total_stores": total_stores,
                "timeseries": timeseries,
            }
            print("[PaymentStats] Response payload prepared.")
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as exc:
            # Log full stack, return safe error response
            logger.exception("Error computing payment stats: %s", exc)
            print("[PaymentStats][ERROR] Exception occurred:", repr(exc))
            return Response(
                {
                    "detail": "Failed to compute payment statistics.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
