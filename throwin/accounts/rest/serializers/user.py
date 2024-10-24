"""Serializer for user"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name",)

    def create(self, validated_data):
        """Set name for existing user"""
        user = self.context["request"].user
        user.name = validated_data["name"]
        user.save()
        return user
