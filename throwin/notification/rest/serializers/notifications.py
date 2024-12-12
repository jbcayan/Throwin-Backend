"""Serializer for notification"""
from rest_framework import serializers

from common.serializers import BaseSerializer

from notification.models import Notification


class NotificationListSerializer(BaseSerializer):
    is_read = serializers.BooleanField(read_only=True)

    class Meta(BaseSerializer.Meta):
        model = Notification
        fields = ["uid", "title", "is_read", "created_at"]


class NotificationDetailSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Notification
        fields = ["uid", "title", "body"]


class NotificationDetailAdminSerializer(NotificationDetailSerializer):
    class Meta(NotificationDetailSerializer.Meta):
        fields = NotificationDetailSerializer.Meta.fields + ["created_by", "updated_by"]

    def create(self, validated_data):
        instance = super().create(validated_data=validated_data)
        instance.created_by = self.context["request"].user
        instance.save(update_fields=["created_by"])

        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data=validated_data)
        instance.updated_by = self.context["request"].user
        instance.save(update_fields=["updated_by"])

        return instance
