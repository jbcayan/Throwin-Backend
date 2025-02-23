"""Serializers for restaurant owner."""
import random
from decimal import Decimal

from django.contrib.auth import authenticate
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import serializers

from accounts.choices import UserKind
from accounts.tasks import send_mail_task
from accounts.utils import generate_admin_account_activation_url

from common.serializers import BaseSerializer
from core.utils import to_decimal

from store.models import Store, StoreUser, RestaurantUser

User = get_user_model()

domain = settings.SITE_DOMAIN


class StoreCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating store."""
    throwin_amounts = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of throwin amounts (e.g., [1000, 5000, 10000]).",
    )

    class Meta:
        model = Store
        fields = [
            "name",
            "location",
            "throwin_amounts",
            "gacha_enabled",
            "banner",
        ]
        read_only_fields = ["restaurant"]

    def validate_throwin_amounts(self, value):
        """
        Custom validation to ensure unique values in the list and proper formatting.
        """
        try:
            decimal_values = []
            for amount in value:
                # Convert string to Decimal and validate range
                decimal_amount = to_decimal(amount)
                if not (Decimal("500.00") <= decimal_amount <= Decimal("49500.00")):
                    raise serializers.ValidationError(
                        "Throwin amount must be between 500.00 and 49500.00."
                    )
                decimal_values.append(decimal_amount)

            # Check for duplicates
            if len(decimal_values) != len(set(decimal_values)):
                raise serializers.ValidationError("Throwin amounts must be unique.")

            return decimal_values

        except (ValueError, TypeError):
            raise serializers.ValidationError(
                "Invalid throwin amount format. Please use numbers only."
            )

    def create(self, validated_data):
        """Create store."""
        throwin_amounts = validated_data.pop('throwin_amounts')
        # Convert Decimal values to properly formatted strings
        validated_data['throwin_amounts'] = ','.join(
            f"{amount:.2f}" for amount in throwin_amounts
        )
        validated_data["restaurant"] = self.context["request"].user.get_restaurant_owner_restaurant
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update store."""
        # Extract throwin_amounts if present and convert to properly formatted string
        if 'throwin_amounts' in validated_data:
            throwin_amounts = validated_data.pop('throwin_amounts')
            validated_data['throwin_amounts'] = ','.join(
                f"{amount:.2f}" for amount in throwin_amounts
            )

        # Remove 'restaurant' to prevent modification
        validated_data.pop("restaurant", None)

        # Update the instance with the validated data
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        # Convert comma-separated string back to a list of formatted strings
        response_data = super().to_representation(instance)
        if instance.throwin_amounts:
            response_data['throwin_amounts'] = [
                f"{Decimal(amount):.2f}"
                for amount in instance.throwin_amounts.split(',')
            ]
        return response_data


class StoreListSerializer(BaseSerializer):
    """Serializer for listing stores."""
    banner = serializers.SerializerMethodField()
    throwin_amounts = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of throwin amounts (e.g., [1000, 5000, 10000]).",
    )

    class Meta:
        model = Store
        fields = [
            "uid",
            "name",
            "code",
            "exposure",
            "banner",
            "throwin_amounts",
        ]
        read_only_fields = ["uid", "name", "code", "exposure", "banner", "throwin_amounts"]

    def get_banner(self, obj) -> dict | None:
        if obj.banner:
            try:
                return {
                    'small': domain + obj.banner.crop['400x400'].url,
                    'medium': domain + obj.banner.crop['600x600'].url,
                    'large': domain + obj.banner.crop['1000x1000'].url,
                    'full_size': domain + obj.banner.url,
                }
            except Exception as e:
                return {'error': str(e)}  # Handle errors gracefully
        return None


    def to_representation(self, instance):
        # Convert comma-separated string back to a list of formatted strings
        response_data = super().to_representation(instance)
        if instance.throwin_amounts:
            response_data['throwin_amounts'] = [
                f"{Decimal(amount):.2f}"
                for amount in instance.throwin_amounts.split(',')
            ]
        return response_data


class StaffListSerializer(BaseSerializer):
    image = serializers.SerializerMethodField()
    uid = serializers.CharField(source='user.uid')
    name = serializers.CharField(source='user.name')
    public_status = serializers.CharField(source='user.public_status')

    class Meta(BaseSerializer.Meta):
        model = User
        fields = [
            "uid",
            "name",
            "public_status",
            "image",
        ]



    def get_image(self, obj) -> dict or None:
        if obj.user.image:
            try:
                return {
                    'small': domain + obj.user.image.crop['400x400'].url,
                    'medium': domain + obj.user.image.crop['600x600'].url,
                    'large': domain + obj.user.image.crop['1000x1000'].url,
                    'full_size': domain + obj.user.image.url,
                }
            except Exception as e:
                return {'error': str(e)}  # Handle errors gracefully
        return None


class StaffCreateSerializer(BaseSerializer):
    """Serializer for creating staff."""
    email = serializers.EmailField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Email of the staff.",
    )
    introduction = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Introduction about the staff.",
    )
    fun_fact = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Fun fact about the staff.",
    )
    store_uid = serializers.CharField(
        write_only=True,  # Ensure it is only used for input, not output
        required=True,
        help_text="The store UID where the staff will be assigned.",
    )
    thank_message = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Thank you message for the user (e.g., 'Thank you for your support')",
    )

    class Meta(BaseSerializer.Meta):
        model = User
        fields = [
            "uid",
            "name",
            "email",
            "public_status",
            "image",
            "introduction",
            "fun_fact",
            "thank_message",
            "store_uid",  # Keep it, but handle manually
        ]
        read_only_fields = ["uid", "email"]

    @transaction.atomic
    def create(self, validated_data):
        """Create staff."""
        # Pop introduction, fun fact, and store_uid from validated data
        introduction = validated_data.pop("introduction", None)
        fun_fact = validated_data.pop("fun_fact", None)
        thank_message = validated_data.pop("thank_message", None)
        store_uid = validated_data.pop("store_uid")  # Extract store UID

        # Get the restaurant of the logged-in restaurant owner
        restaurant = self.context["request"].user.get_restaurant_owner_restaurant

        # Retrieve the store object using UID
        try:
            store = Store.objects.get(
                uid=store_uid,
                restaurant_id=restaurant.id,
            )
        except Store.DoesNotExist:
            raise serializers.ValidationError({
                "store_uid": "Invalid store UID provided."
            })

        # Generate email if not provided
        email = validated_data.get("email", None)
        if not email:
            count = User.objects.all().count()
            email = f"staff.{store.code}.{count}@gmail.com"
            if User.objects.filter(email=email).exists():
                # Generate a random 6-digit number and character and append to the email
                random_number_char = ''.join(random.choices('0123456789abcdefghijklmnopqrstuvwxyz', k=6))
                email = f"staff.{store.code}.{random_number_char}@gmail.com"

        validated_data["email"] = email

        # Add kind to validated data
        validated_data["kind"] = UserKind.RESTAURANT_STAFF

        # Create staff using the validated data
        staff = super().create(validated_data)

        # Update user profile
        profile = staff.profile
        profile.introduction = introduction
        profile.fun_fact = fun_fact
        profile.thank_message = thank_message
        profile.save(update_fields=['introduction', 'fun_fact', 'thank_message'])

        # Save extra fields in serializer context (not in DB)
        self.context["extra_fields"] = {
            "introduction": introduction,
            "fun_fact": fun_fact,
            "thank_message": thank_message,
        }

        # Associate staff with restaurant
        RestaurantUser.objects.get_or_create(
            restaurant_id=restaurant.id,
            user_id=staff.id,
            role=UserKind.RESTAURANT_STAFF,
        )

        # Associate staff with store
        StoreUser.objects.get_or_create(
            user_id=staff.id,
            store_id=store.id,
            role=UserKind.RESTAURANT_STAFF,
        )

        return staff

    def to_representation(self, instance):
        """Modify response to include write-only fields."""
        data = super().to_representation(instance)

        # Retrieve extra fields from context and add to response
        extra_fields = self.context.get("extra_fields", {})
        data.update(extra_fields)

        return data


class StaffUserSerializer(serializers.ModelSerializer):
    uid = serializers.CharField(source="user.uid")
    name = serializers.CharField(source="user.name")
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = StoreUser
        fields = ["uid", "name", "email"]


class GachaHistorySerializer(serializers.Serializer):
    uid = serializers.UUIDField()
    name = serializers.CharField()
    banner = serializers.ImageField()
    gacha_settings = serializers.CharField()
    gold_issued = serializers.IntegerField()
    gold_used = serializers.IntegerField()
    silver_issued = serializers.IntegerField()
    silver_used = serializers.IntegerField()
    bronze_issued = serializers.IntegerField()
    bronze_used = serializers.IntegerField()


class SalesAgentCreateSerializer(serializers.Serializer):
    # user details
    name = serializers.CharField(max_length=100, required=True)
    phone_number = serializers.CharField(max_length=15, required=True)
    email = serializers.EmailField(required=True)
    # profile details
    post_code = serializers.CharField(max_length=10, required=True)
    address = serializers.CharField(max_length=255, required=True)
    company_name = serializers.CharField(max_length=100, required=True)
    invoice_number = serializers.CharField(max_length=20, required=True)
    corporate_number = serializers.CharField(max_length=20, required=True)


    def create(self, validated_data):
        post_code = validated_data.pop("post_code", None)
        address = validated_data.pop("address", None)
        company_name = validated_data.pop("company_name", None)
        invoice_number = validated_data.pop("invoice_number", None)
        corporate_number = validated_data.pop("corporate_number", None)

        name = validated_data.pop("name", None)
        phone_number = validated_data.pop("phone_number", None)
        email = validated_data.pop("email", None)

        user = User.objects.create_user(
            name=name,
            phone_number=phone_number,
            email=email,
            kind=UserKind.SALES_AGENT
        )
        user.set_password(phone_number)
        user.save()

        profile = user.profile
        profile.post_code = post_code
        profile.address = address
        profile.company_name = company_name
        profile.invoice_number = invoice_number
        profile.corporate_number = corporate_number
        profile.save(update_fields=[
            'post_code',
            'address',
            'company_name',
            'invoice_number',
            'corporate_number'
        ])

        return user

class ChangeRestaurantOwnerNameSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)

    def create(self, validated_data):
        name = validated_data.pop("name", None)
        user = self.context["request"].user
        user.name = name
        user.save(
            update_fields=["name"]
        )
        return user

class RestaurantOwnerChangeEmailRequestSerializer(serializers.Serializer):
    """
    Serializer for changing the email of the restaurant owner
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user

        # Authenticate user with provided password
        if not user.check_password(data['password']):
            raise serializers.ValidationError({
                "detail": "Incorrect password."
            })

        if user.email == data['email']:
            raise serializers.ValidationError({"email": "New email is the same as the current email."})

        # Check if the new email is already in use
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})

        return data

    def save(self):
        user = self.context['request'].user
        new_email = self.validated_data['email']

        # Generate activation link
        activation_url = generate_admin_account_activation_url(user, new_email)

        # Send activation email
        subject = "Email Change Request"
        message = f"Please click the following link to verify your new email: {activation_url}"
        send_mail_task.delay(subject, message, new_email)
