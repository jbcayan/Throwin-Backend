"""Views for restaurant owner."""
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.choices import UserKind

from common.permissions import (
    CheckAnyPermission,
    IsRestaurantOwnerUser,
    IsSuperAdminUser,
    IsFCAdminUser,
    IsGlowAdminUser,
)

from store.filters import StoreFilter, StaffFilter
from store.models import Store, RestaurantUser, StoreUser, Restaurant
from store.rest.serializers.restaurant_owner import (
    StoreCreateSerializer,
    StoreListSerializer,
    StaffListSerializer,
    StaffCreateSerializer,
)

@extend_schema(
    summary="List and Create Stores for Restaurant Owner",
    methods=["GET", "POST"],
)
class StoreListCreateView(generics.ListCreateAPIView):
    """View for restaurant owner to create or list stores."""

    filterset_class = StoreFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    available_permission_classes = (
        IsRestaurantOwnerUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StoreCreateSerializer
        return StoreListSerializer

    def get_queryset(self):
        # Get the restaurant of the logged in restaurant owner
        try:
            user_restaurant = self.request.user.get_restaurant_owner_restaurant
        except AttributeError as e:
            return Store.objects.none()

        return Store().get_all_actives().filter(
            restaurant_id=user_restaurant.id
        ).only(
            "uid",
            "name",
            "code",
            "restaurant",
            "exposure",
            "banner",
        ).select_related(
            "restaurant"
        )
    
class StaffListCreateView(generics.ListCreateAPIView):
    """View for restaurant owner to create or list staff."""
    
    filterset_class = StaffFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StaffCreateSerializer
        return StaffListSerializer

    available_permission_classes = (
        IsRestaurantOwnerUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_queryset(self):
        # Get the restaurant of the logged in restaurant owner
        try:
            user_restaurant = self.request.user.get_restaurant_owner_restaurant
        except AttributeError as e:
            return RestaurantUser.objects.none()

        return (
            RestaurantUser.objects.filter(
                restaurant=user_restaurant, role=UserKind.RESTAURANT_STAFF
            )
            .select_related("user")
            .only(
                "user__uid",
                "user__name",
                "user__email",
                "user__image",
                "user__public_status",
                "user__username",
                "user__phone_number",
            )
        )
