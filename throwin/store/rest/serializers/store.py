"""Serializers for store."""

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

    class Meta(BaseSerializer.Meta):
        model = Store
        fields = [
            "uid",
            "name",
            "code",
            "description",
            "logo",
            "banner"
        ]
        read_only_fields = ["uid"]
