from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from accounts.choices import UserKind
from common.permissions import IsConsumerUser
from store.rest.serializers.store_stuff import StoreStuffListSerializer

User = get_user_model()


@extend_schema(
    summary="Store stuff list",
    description="Get store stuff list based on store code",
    responses=StoreStuffListSerializer
)
class StoreStuffList(generics.ListAPIView):
    serializer_class = StoreStuffListSerializer
    permission_classes = [IsConsumerUser]

    def get_queryset(self):
        if store_code := self.kwargs.get("store_code", None):
            return User().get_all_actives().filter(
                store__code=store_code,
                kind=UserKind.RESTAURANT_STUFF
            ).select_related(
                "profile",
                "store"
            )
        else:
            return Response({
                "detail": "Store code is required"
            }, status=status.HTTP_400_BAD_REQUEST)