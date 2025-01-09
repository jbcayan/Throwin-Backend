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
    CheckAnyPermission, IsRestaurantOwnerUser
)


class StoreListCreate(generics.ListCreateAPIView):
    serializer_class = StoreSerializer

    available_permission_classes = ()

    def get_permissions(self):
        if self.request.method == "POST":
            self.available_permission_classes = (
                IsFCAdminUser,
                IsGlowAdminUser,
                IsRestaurantOwnerUser
            )
        else:
            self.available_permission_classes = (
                IsConsumerOrGuestUser,
                IsConsumerUser,
                IsGlowAdminUser,
                IsFCAdminUser,
            )
        return (CheckAnyPermission(),)

    def get_queryset(self):
        return Store().get_all_actives()


class StoreDetailUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StoreSerializer
    permission_classes = (permissions.AllowAny,)

    def get_object(self):
        try:
            return Store().get_all_actives().get(code=self.kwargs["code"])
        except Store.DoesNotExist:
            return Response({
                "detail": "Store not found"
            }, status=status.HTTP_404_NOT_FOUND)
