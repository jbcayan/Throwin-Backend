from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema

from rest_framework import generics, status
from rest_framework.response import Response

from accounts.choices import UserKind

from common.permissions import (
    IsConsumerUser,
    CheckAnyPermission,
    IsConsumerOrGuestUser,
    IsGlowAdminUser,
    IsFCAdminUser,
    IsSuperAdminUser
)

from store.rest.serializers.store_stuff import (
    StoreStuffListSerializer,
    StoreUserSerializer,
)

from store.models import Store, StoreUser, Restaurant, RestaurantUser

User = get_user_model()


@extend_schema(
    summary="Store stuff list",
    description="Get store stuff list based on store code",
    responses=StoreUserSerializer
)
class StoreStuffList(generics.ListAPIView):
    serializer_class = StoreUserSerializer
    available_permission_classes = (
        IsConsumerOrGuestUser,
        IsConsumerUser,
        IsGlowAdminUser,
        IsFCAdminUser,
        IsSuperAdminUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_queryset(self):
        """
        Get users associated with a specific store based on the store code
        via StoreUser model.
        """
        code = self.kwargs.get("code", None)
        if not code:
            return Response({
                "detail": "No code provided"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            return StoreUser.objects.filter(
                store__code=code, role=UserKind.RESTAURANT_STAFF
            ).select_related(
                "user",
                "user__profile",
                "store",
                "store__restaurant",
            )
        except Exception as e:
            return Response({
                "detail": "Invalid code provided",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
