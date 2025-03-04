"""Views for store"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework import permissions

from store.models import Store
from store.rest.serializers.stores import StoreSerializer

from common.permissions import (
    IsConsumerOrGuestUser,
    IsConsumerUser,
    IsGlowAdminUser,
    IsFCAdminUser,
    CheckAnyPermission,
    IsRestaurantOwnerUser,
    IsSuperAdminUser,
)


class StoreList(generics.ListAPIView):
    serializer_class = StoreSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        return Store().get_all_actives()


class StoreDetail(generics.RetrieveAPIView):
    serializer_class = StoreSerializer

    permission_classes = (permissions.AllowAny,)

    def get_object(self):
        try:
            return Store().get_all_actives().get(code=self.kwargs["code"])
        except Store.DoesNotExist:
            return Response({
                "detail": "Store not found"
            }, status=status.HTTP_404_NOT_FOUND)
