"""Serializer for user"""

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers

from accounts.tasks import send_mail_task
from accounts.utils import generate_verification_token

from versatileimagefield.serializers import VersatileImageFieldSerializer

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


class EmailChangeRequestSerializer(serializers.Serializer):
    new_email = serializers.EmailField()

    def validate_new_email(self, value):
        """Ensure that new email is not already in use"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use")
        return value

    def save(self, user):
        new_email = self.validated_data["new_email"]

        # generate token for email verification
        token = generate_verification_token(user, new_email)

        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"

        # Send a verification email to the new email address
        send_mail_task(
            subject="Verify Email",
            message=f"Please click the link below to verify your email. {verification_url}",
            to_email=new_email,
        )
