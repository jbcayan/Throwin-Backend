"""Views for restaurant owner."""
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from common.permissions import (
    CheckAnyPermission,
    IsRestaurantOwnerUser,
    IsSuperAdminUser,
    IsFCAdminUser,
    IsGlowAdminUser,
)

from store.filters import StoreFilter
from store.models import Store
from store.rest.serializers.restaurant_owner import (
    StoreCreateSerializer,
    StoreListSerializer
)

class StoreListCreateView(generics.ListCreateAPIView):
    """View for restaurant owner to create or list stores."""

    serializer_class = StoreCreateSerializer

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