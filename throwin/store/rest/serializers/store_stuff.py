from django.contrib.auth import get_user_model
from rest_framework import serializers
from versatileimagefield.serializers import VersatileImageFieldSerializer

User = get_user_model()


class StoreStuffListSerializer(serializers.ModelSerializer):
    """Serializer to represent restaurant stuff list with profile details."""

    introduction = serializers.CharField(
        source="profile.introduction",
        allow_blank=True,
        allow_null=True,
    )
    score = serializers.IntegerField(
        source="profile.total_score",
        default=0
    )
    image = VersatileImageFieldSerializer(
        sizes='profile_image'
    )

    class Meta:
        model = User
        fields = ("uid", "name", "introduction", "score", "image")