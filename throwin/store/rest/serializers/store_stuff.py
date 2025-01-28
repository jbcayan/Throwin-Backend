from django.contrib.auth import get_user_model

from rest_framework import serializers

from accounts.rest.serializers.user import StaffDetailForConsumerSerializer
from versatileimagefield.serializers import VersatileImageFieldSerializer

from store.models import StoreUser

from django.conf import settings

User = get_user_model()

domain = settings.SITE_DOMAIN


class StoreStuffListSerializer(StaffDetailForConsumerSerializer):
    """Serializer to represent a restaurant stuff list with profile details."""

    fun_fact = serializers.CharField(
        source="profile.fun_fact",
        allow_blank=True,
        allow_null=True,
    )
    image = serializers.SerializerMethodField()

    class Meta(StaffDetailForConsumerSerializer.Meta):
        fields = (
            "uid",
            "name",
            "username",
            "introduction",
            "score",
            "image",
            "fun_fact",
        )

    def get_image(self, obj) -> dict or None:
        if obj.image:
            try:
                return {
                    'small': domain + obj.image.crop['400x400'].url,
                    'medium': domain + obj.image.crop['600x600'].url,
                    'large': domain + obj.image.crop['1000x1000'].url,
                    'full_size': domain + obj.image.url,
                }
            except Exception as e:
                return {'error': str(e)}  # Handle errors gracefully
        return None


class StoreUserSerializer(serializers.ModelSerializer):
    uid = serializers.CharField(source="user.uid")
    name = serializers.CharField(source="user.name")
    username = serializers.CharField(source="user.username")
    introduction = serializers.CharField(
        source="user.profile.introduction", allow_null=True, allow_blank=True
    )
    score = serializers.IntegerField(source="user.profile.total_score", default=0)
    fun_fact = serializers.CharField(
        source="user.profile.fun_fact", allow_null=True, allow_blank=True
    )
    store_name = serializers.CharField(source="store.name")
    store_uid = serializers.CharField(source="store.uid")
    restaurant_uid = serializers.CharField(source="store.restaurant.uid")
    image = serializers.SerializerMethodField()

    class Meta:
        model = StoreUser
        fields = [
            "uid",
            "name",
            "username",
            "introduction",
            "score",
            "image",
            "fun_fact",
            "store_name",
            "store_uid",
            "restaurant_uid",
        ]

    def get_image(self, obj) -> dict or None:
        if obj.user.image:
            try:
                return {
                    'small': domain + obj.user.image.crop['400x400'].url,
                    'medium': domain + obj.user.image.crop['600x600'].url,
                    'large': domain + obj.user.image.crop['1000x1000'].url,
                    'full_size': domain + obj.user.image.url,
                }
            except Exception as e:
                return {'error': str(e)}  # Handle errors gracefully
        return None
