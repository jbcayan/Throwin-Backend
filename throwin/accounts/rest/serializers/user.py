"""Serializer for user"""

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers

from accounts.choices import UserKind
from accounts.models import Like
from accounts.tasks import send_mail_task
from accounts.utils import generate_verification_token

from versatileimagefield.serializers import VersatileImageFieldSerializer

from common.serializers import BaseSerializer

from django.conf import settings

domain = settings.SITE_DOMAIN

User = get_user_model()


class UserNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name",)

    def create(self, validated_data):
        """Set name for existing user"""
        name = validated_data["name"]
        # if User.objects.filter(name=name).exists():
        #     raise serializers.ValidationError("Name is already in use")

        user = self.context["request"].user
        user.name = name
        user.save()
        return user


class GuestNameSerializer(serializers.Serializer):
    name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )


class EmailChangeRequestSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate_new_email(self, value):
        """Ensure that new email is not already in use"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use")
        return value

    def save(self, user):
        new_email = self.validated_data["new_email"]
        password = self.validated_data["password"]

        if not user.check_password(password):
            raise serializers.ValidationError({
                "detail": "Incorrect password."
            })

        # generate token for email verification
        token = generate_verification_token(user, new_email)

        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"

        send_mail_task.delay(
            subject="Verify Email",
            message=f"Please click the link below to verify your email. {verification_url}",
            to_email=new_email
        )


class StaffDetailForConsumerSerializer(BaseSerializer):
    """Serializer to represent restaurant stuff details."""

    introduction = serializers.CharField(
        source="profile.introduction",
        allow_blank=True,
        allow_null=True,
    )
    score = serializers.IntegerField(
        source="profile.total_score",
        default=0
    )
    image = serializers.SerializerMethodField()
    fun_fact = serializers.CharField(
        source="profile.fun_fact",
        allow_blank=True,
        allow_null=True,
        help_text="Short fun fact about the user (e.g., 'Eating and laughing')"
    )

    class Meta(BaseSerializer.Meta):
        model = User
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


class MeSerializer(BaseSerializer):
    """This serializer is used to represent the current user's details."""
    image = serializers.SerializerMethodField()
    introduction = serializers.CharField(
        source="profile.introduction",
        allow_blank=True,
        allow_null=True,
    )
    address = serializers.CharField(
        source="profile.address",
        allow_blank=True,
        allow_null=True,
    )
    total_score = serializers.IntegerField(
        source="profile.total_score",
        default=0
    )
    fun_fact = serializers.CharField(
        source="profile.fun_fact",
        allow_blank=True,
        allow_null=True,
        help_text="Short fun fact about the user (e.g., 'Eating and laughing')"
    )

    class Meta(BaseSerializer.Meta):
        model = User
        fields = (
            "id",
            "uid",
            "name",
            "email",
            "phone_number",
            "username",
            "image",
            "auth_provider",
            "kind",
            "introduction",
            "address",
            "total_score",
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

    def to_representation(self, instance):
        """Customize the fields based on the user kind."""
        print("I am here")
        representation = super().to_representation(instance)

        # Check if the user's kind is not RESTAURANT_STAFF
        if instance.kind != UserKind.RESTAURANT_STAFF:
            # Keep only the basic fields for non-restaurant staff users
            fields_to_keep = {
                "id", "uid", "name", "email", "phone_number", "username", "image", "auth_provider", "kind"
            }
            representation = {key: representation[key] for key in fields_to_keep if key in representation}

        return representation
