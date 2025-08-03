"""Views for store"""
from django.http import Http404
from rest_framework import generics, status, permissions
from rest_framework.response import Response

from store.models import Store
from store.rest.serializers.stores import StoreSerializer


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
            store = Store().get_all_actives().get(
                code=self.kwargs["code"]
            )
            return store
        except Store.DoesNotExist:
            raise Http404("Store not found")
