"""Common serializers for this project."""

from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """Base serializer class."""

    class Meta:
        model = None
        fields = ["uid"]
