from django.contrib.auth import get_user_model

from rest_framework import serializers

from accounts.rest.serializers.user import StaffDetailForConsumerSerializer
from versatileimagefield.serializers import VersatileImageFieldSerializer

from store.models import StoreUser

User = get_user_model()


class StoreStuffListSerializer(StaffDetailForConsumerSerializer):
    """Serializer to represent a restaurant stuff list with profile details."""

    fun_fact = serializers.CharField(
        source="profile.fun_fact",
        allow_blank=True,
        allow_null=True,
    )

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

    def get_image(self, obj):
        try:
            if obj.image:
                return VersatileImageFieldSerializer(obj.image, context=self.context).data
            return None
        except (FileNotFoundError, ValueError):
            # Return None if the image file is not found or another error occurs
            return None


class StoreUserSerializer(serializers.ModelSerializer):
    uid = serializers.CharField(source="user.uid")
    name = serializers.CharField(source="user.name")
    username = serializers.CharField(source="user.username")
    introduction = serializers.CharField(
        source="user.profile.introduction", allow_null=True, allow_blank=True
    )
    score = serializers.IntegerField(source="user.profile.total_score", default=0)
    image = VersatileImageFieldSerializer(sizes="profile_image", source="user.image")
    fun_fact = serializers.CharField(
        source="user.profile.fun_fact", allow_null=True, allow_blank=True
    )
    store_name = serializers.CharField(source="store.name")
    store_uid = serializers.CharField(source="store.uid")
    restaurant_uid = serializers.CharField(source="store.restaurant.uid")

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

    # def get_image(self, obj):
    #     try:
    #         if obj.user.image:
    #             return VersatileImageFieldSerializer(obj.user.image, context=self.context).data
    #         return None
    #     except (FileNotFoundError, ValueError):
    #         # Return None if the image file is not found or another error occurs
    #         return None
