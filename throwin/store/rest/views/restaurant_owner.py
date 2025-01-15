"""Views for restaurant owner."""

from rest_framework import status
from rest_framework.response import Response

from rest_framework import generics

from common.permissions import (
    IsConsumerUser,
    CheckAnyPermission,
    IsConsumerOrGuestUser,
    IsGlowAdminUser,
    IsFCAdminUser,
    IsSuperAdminUser, IsRestaurantOwnerUser
)

from store.models import Restaurant, RestaurantUser, Store, StoreUser

from store.rest.serializers.restaurant_owner import RestaurantStoresSerializer


class RestaurantStoresView(generics.ListAPIView):
    """View for restaurant owner to see stores."""

    serializer_class = RestaurantStoresSerializer
    available_permission_classes = (
        IsRestaurantOwnerUser,
    )
    permission_classes = (CheckAnyPermission,)

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
            "restaurant"
        ).select_related(
            "restaurant"
        )
