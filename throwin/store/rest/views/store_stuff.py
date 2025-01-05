from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema

from rest_framework import generics, status
from rest_framework.response import Response

from accounts.choices import UserKind

from common.permissions import IsConsumerUser, CheckAnyPermission, IsConsumerOrGuestUser, IsAdminUser, IsSuperAdminUser

from store.rest.serializers.store_stuff import StoreStuffListSerializer

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
        IsAdminUser,
        IsSuperAdminUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_queryset(self):
        """
        Get store stuff list based on store code or restaurant slug
        :return: List of store stuff
        """
        if not (code := self.kwargs.get("code", None)):
            return Response({
                    "detail": "No code provided"
                }, status=status.HTTP_400_BAD_REQUEST)
        try:
            print("Code: ", code)
            query_sets = User().get_all_actives().filter(
                store__code=code,
                kind=UserKind.RESTAURANT_STAFF
            ).select_related(
                "profile",
                "store",
                "restaurant"
            )
            if not query_sets.exists():
                query_sets = User().get_all_actives().filter(
                    restaurant__slug=code,
                    kind=UserKind.RESTAURANT_STAFF
                ).select_related(
                    "profile",
                    "store",
                    "restaurant"
                )
            return query_sets
        except Exception as e:
            return Response({
                "detail": "Invalid code provided"
            }, status=status.HTTP_400_BAD_REQUEST)
