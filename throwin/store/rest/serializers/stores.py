"""Serializers for store."""
from django.conf import settings

from rest_framework import serializers

from common.serializers import BaseSerializer

from store.models import Store

from versatileimagefield.serializers import VersatileImageFieldSerializer

domain = settings.SITE_DOMAIN

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

    def get_restaurant_uid(self, obj) -> str or None:
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
    
    def get_banner(self, obj) -> dict or None:
        if obj.banner:
            try:
                return {
                    'small': domain + obj.banner.crop['400x400'].url,
                    'medium': domain + obj.banner.crop['600x600'].url,
                    'large': domain + obj.banner.crop['1000x1000'].url,
                    'full_size': domain + obj.banner.url,
                }
            except Exception as e:
                return {'error': str(e)}  # Handle errors gracefully
        return None
