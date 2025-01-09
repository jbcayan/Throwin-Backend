"""Serializers for store."""

from rest_framework import serializers
from common.serializers import BaseSerializer

from store.models import Store

from versatileimagefield.serializers import VersatileImageFieldSerializer


class StoreSerializer(BaseSerializer):
    """Serializer for store."""

    logo = VersatileImageFieldSerializer(
        sizes="store_logo",
        required=False
    )
    banner = VersatileImageFieldSerializer(
        sizes="store_banner",
        required=False
    )
    code = serializers.CharField(
        max_length=20,
        required=False
    )
    restaurant_uid = serializers.SerializerMethodField()

    def get_restaurant_uid(self, obj):
        return obj.restaurant.uid if obj.restaurant else None

    class Meta(BaseSerializer.Meta):
        model = Store
        fields = [
            "uid",
            "name",
            "code",
            "description",
            "logo",
            "banner",
            "restaurant_uid",
        ]
        read_only_fields = ["uid"]

    def create(self, validated_data):
        instance = super().create(validated_data=validated_data)
        # instance.user_created = self.context["request"].user
        # instance.save(update_fields=["user_created"])

        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data=validated_data)
        # instance.user_updated = self.context["request"].user
        # instance.save(update_fields=["user_updated"])

        return instance
