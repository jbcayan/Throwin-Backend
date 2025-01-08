from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema

from rest_framework import generics, status
from rest_framework.response import Response

from accounts.choices import UserKind

from common.permissions import IsConsumerUser, CheckAnyPermission, IsConsumerOrGuestUser, IsGlowAdminUser, IsFCAdminUser

from store.rest.serializers.store_stuff import StoreStuffListSerializer

from store.models import Store, StoreUser, Restaurant, RestaurantUser

User = get_user_model()


@extend_schema(
    summary="Store stuff list",
    description="Get store stuff list based on store code",
    responses=StoreStuffListSerializer
)
class StoreStuffList(generics.ListAPIView):
    serializer_class = StoreStuffListSerializer
    available_permission_classes = (
        IsConsumerOrGuestUser,
        IsConsumerUser,
        IsGlowAdminUser,
        IsFCAdminUser,
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
            print("Code: ", code)
            # Filter StoreUser objects and fetch related User objects
            store_users = StoreUser.objects.filter(
                store__code=code,
                role=UserKind.RESTAURANT_STAFF
            ).select_related("user", "store")

            # Extract and return associated User instances
            return User.objects.filter(id__in=store_users.values_list("user_id", flat=True)).distinct()
        except Exception as e:
            return Response({
                "detail": "Invalid code provided",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
