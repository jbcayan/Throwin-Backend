"""Serializers for restaurant owner."""
from decimal import Decimal

from django.conf import settings

from rest_framework import serializers

from common.serializers import BaseSerializer

from store.models import Store

domain = settings.SITE_DOMAIN



class StoreCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating store."""
    throwin_amounts = serializers.ListField(
        child=serializers.DecimalField(
            max_digits=10,
            decimal_places=2,
            min_value=Decimal("500.00"),
            max_value=Decimal("49500.00"),
        ),
        help_text="List of throwin amounts (e.g., [1000, 5000, 10000]).",
    )

    class Meta:
        model = Store
        fields = [
            "name",
            "location",
            "throwin_amounts",
            "gacha_enabled",
            "banner",
        ]
        read_only_fields = ["restaurant"]

    def validate_throwin_amounts(self, value):
        """
        Custom validation to ensure unique values in the list.
        """
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Throwin amounts must be unique.")
        return value

    def create(self, validated_data):
        """Create store."""
        throwin_amounts = validated_data.pop('throwin_amounts')
        validated_data['throwin_amounts'] = ','.join(map(str, throwin_amounts))
        validated_data["restaurant"] = self.context["request"].user.get_restaurant_owner_restaurant
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update store."""
        if throwin_amounts := validated_data.pop('throwin_amounts', None):
            validated_data['throwin_amounts'] = ','.join(map(str, throwin_amounts))
        validated_data.pop("restaurant", None)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        # Convert comma-separated string back to a list for the response
        response_data = super().to_representation(instance)
        if instance.throwin_amounts:
            response_data['throwin_amounts'] = list(instance.throwin_amounts.split(','))
        return response_data


class StoreListSerializer(BaseSerializer):
    """Serializer for listing stores."""
    banner = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = [
            "uid",
            "name",
            "code",
            "exposure",
            "banner",
        ]
        read_only_fields = ["uid"]

    def get_banner(self, obj) -> dict | None:
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
