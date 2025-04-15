"""Serializer for user"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from accounts.choices import UserKind
from accounts.models import TemporaryUser
from accounts.tasks import send_mail_task
from accounts.utils import generate_verification_token
from common.serializers import BaseSerializer
from review.models import Review, Reply

domain = settings.SITE_DOMAIN

User = get_user_model()


class AccountActivationSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, data):
        try:
            uid = force_str(urlsafe_base64_decode(data['uidb64']))
            temp_user = TemporaryUser.objects.get(pk=uid, token=data['token'])

            # Check if token is expired
            TOKEN_EXPIRATION_HOURS = 48
            if temp_user.created_at + timedelta(hours=TOKEN_EXPIRATION_HOURS) <= timezone.now():
                raise serializers.ValidationError("Token Expired")

            data['temp_user'] = temp_user
            return data
        except (TypeError, ValueError, OverflowError, TemporaryUser.DoesNotExist):
            raise serializers.ValidationError("Invalid Token or User")


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


class EmailChangeTokenSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, data):
        try:
            access_token = AccessToken(data['token'])
            user_id = access_token.get("user_id")
            new_email = access_token.get("new_email")

            if not user_id or not new_email:
                raise serializers.ValidationError("Invalid token data")

            data['user_id'] = user_id
            data['new_email'] = new_email
            return data

        except Exception:
            raise serializers.ValidationError("Invalid token")



class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for representing a review associated with a staff member.
    """
    class Meta:
        model = Review
        fields = ("consumer_name", "message", "created_at")

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
    store_code = serializers.SerializerMethodField()
    store_uid = serializers.SerializerMethodField()
    throwin_amounts = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

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
            "store_code",
            "store_uid",
            "throwin_amounts",
            "reviews",
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

    def get_store_code(self, obj) -> str or None:
        """
        Get the store code associated with the staff member.
        """
        staff_store = obj.get_staff_store
        if staff_store:
            return staff_store.code
        return None

    def get_store_uid(self, obj) -> str or None:
        """
        Get the store uid associated with the staff member.
        """
        staff_store = obj.get_staff_store
        if staff_store:
            return staff_store.uid
        return None

    def get_throwin_amounts(self, obj) -> list or None:
        """Get the throwin amounts associated with the staff member's store."""
        staff_store = obj.get_staff_store
        if staff_store and staff_store.throwin_amounts:
            return staff_store.throwin_amounts.split(",")  # Convert string to list
        return []

    def get_reviews(self, obj) -> list:
        """
        Retrieve a list of reviews related to the given staff member by matching
        the staff_uid (from Review) with the user's uid.
        """
        # Fetch reviews whose staff_uid equals the user uid
        reviews_qs = Review.objects.filter(staff_uid=obj.uid).order_by("-created_at")
        # Serialize the reviews and return the data
        return ReviewSerializer(reviews_qs, many=True, context=self.context).data


class MeSerializer(BaseSerializer):
    """This serializer is used to represent the current user's details."""
    image = serializers.SerializerMethodField()
    introduction = serializers.CharField(
        source="profile.introduction", allow_blank=True, allow_null=True,
    )
    address = serializers.CharField(
        source="profile.address", allow_blank=True, allow_null=True,
    )
    total_score = serializers.IntegerField(
        source="profile.total_score", default=0
    )
    fun_fact = serializers.CharField(
        source="profile.fun_fact", allow_blank=True, allow_null=True,
        help_text="Short fun fact about the user (e.g., 'Eating and laughing')"
    )
    company_name = serializers.CharField(
        source="profile.company_name", allow_blank=True, allow_null=True
    )

    class Meta(BaseSerializer.Meta):
        model = User
        fields = (
            "id", "uid", "name", "email", "phone_number", "username", "image",
            "auth_provider", "kind", "introduction", "address", "total_score",
            "fun_fact", "company_name"
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
        representation = super().to_representation(instance)

        # Check if the user's kind is not RESTAURANT_STAFF
        if instance.kind != UserKind.RESTAURANT_STAFF:
            # Keep only the basic fields for non-restaurant staff users
            fields_to_keep = {
                "id", "uid", "name", "email", "phone_number", "username",
                "image", "auth_provider", "kind"
            }
            representation = {key: representation[key] for key in fields_to_keep if key in representation}

        # Include company_name for RESTAURANT_OWNER and SALES_AGENT
        if instance.kind in {UserKind.RESTAURANT_OWNER, UserKind.SALES_AGENT}:
            representation['company_name'] = instance.profile.company_name

        return representation


class StaffLikeToggleSerializer(serializers.Serializer):
    uid = serializers.UUIDField()

    def validate_uid(self, value):
        # Validate that the staff member exists and is active
        staff = get_object_or_404(
            User,
            uid=value,
            is_active=True,
            kind=UserKind.RESTAURANT_STAFF
        )
        return staff


class GetRestaurantOwnerReplySerializer(serializers.ModelSerializer):
    """
    Serializer for replies made by a restaurant owner.
    """

    class Meta:
        model = Reply
        fields = ["uid", "message", "created_at"]
