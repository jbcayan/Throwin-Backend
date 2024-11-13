from django.contrib.auth import get_user_model

from rest_framework import serializers

from accounts.rest.serializers.user import StuffDetailForConsumerSerializer
from versatileimagefield.serializers import VersatileImageFieldSerializer

User = get_user_model()


class StoreStuffListSerializer(StuffDetailForConsumerSerializer):
    """Serializer to represent restaurant stuff list with profile details."""

    fun_fact = serializers.CharField(
        source="profile.fun_fact",
        allow_blank=True,
        allow_null=True,
    )

    class Meta(StuffDetailForConsumerSerializer.Meta):
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
