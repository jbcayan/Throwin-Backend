"""Views for store"""
from rest_framework import generics, status
from rest_framework.response import Response

from store.models import Store
from store.rest.serializers.stores import StoreSerializer

from common.permissions import (
    IsConsumerOrGuestUser,
    IsConsumerUser,
    IsAdminUser,
    IsSuperAdminUser,
    CheckAnyPermission
)


class StoreListCreate(generics.ListCreateAPIView):
    serializer_class = StoreSerializer

    available_permission_classes = ()

    def get_permissions(self):
        if self.request.method == "POST":
            self.available_permission_classes = (
                IsSuperAdminUser,
                IsAdminUser,
            )
        else:
            self.available_permission_classes = (
                IsConsumerOrGuestUser,
                IsConsumerUser,
                IsAdminUser,
                IsSuperAdminUser,
            )
        return (CheckAnyPermission(),)

    def get_queryset(self):
        queryset = Store().get_all_actives()
        return queryset


class StoreDetailUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StoreSerializer

    available_permission_classes = ()

    def get_permissions(self):
        if self.request.method == "PUT":
            self.available_permission_classes = (
                IsAdminUser,
                IsSuperAdminUser,
            )
        else:
            self.available_permission_classes = (
                IsConsumerOrGuestUser,
                IsConsumerUser,
                IsAdminUser,
                IsSuperAdminUser,
            )
        return (CheckAnyPermission(),)

    def get_object(self):
        queryset = Store().get_all_actives().get(
            code=self.kwargs["code"]
        )
        return queryset
