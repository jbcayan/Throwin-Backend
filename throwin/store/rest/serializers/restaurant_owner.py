"""Serializers for restaurant owner."""

from rest_framework import serializers
from common.serializers import BaseSerializer

from store.models import Restaurant, RestaurantUser, Store, StoreUser

from versatileimagefield.serializers import VersatileImageFieldSerializer


class RestaurantStoresSerializer(BaseSerializer):

    class Meta:
        model = Store
        fields = [
            "uid",
            "name",
            "code",
        ]
        read_only_fields = ["uid"]
