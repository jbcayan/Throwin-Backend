"""Serializers for User model."""

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from rest_framework import serializers

from accounts.choices import UserKind
from accounts.models import TemporaryUser

User = get_user_model()



def validate_password_complexity(value):
    """Validate that the password is at least 8 characters long
    and contains one Upper case letter, one lower case letter, one number"""
    errors = []
    if len(value) < 8:
        errors.append("at least 8 characters")
    if re.search(r"\d", value) is None:
        errors.append("one number")
    if re.search(r"[A-Z]", value) is None:
        errors.append("one uppercase letter")
    if re.search(r"[a-z]", value) is None:
        errors.append("one lowercase letter")
    if errors:
        raise ValidationError("Password must contain: " + ", ".join(errors) + ".")

class UserRegisterSerializerWithEmail(serializers.ModelSerializer):
    """Serializer for user registration with email."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password_complexity],
    )
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = TemporaryUser
        fields = (
            "email",
            "password",
            "confirm_password",
        )

    def validate(self, attrs):
        """Ensure password and confirm_password match."""
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords didn't match."})
        return attrs

    def create(self, validated_data):
        """Create a new user."""
        validated_data.pop("confirm_password")
        return TemporaryUser.objects.create(
            email=validated_data["email"],
            password=validated_data["password"],
            kind=UserKind.CONSUMER,
        )


class CheckEmailAlreadyExistsSerializer(serializers.Serializer):
    """Serializer for checking if email already exists."""
    email = serializers.EmailField()

    class Meta:
        fields = ("email",)

    def validate(self, attrs):
        """Ensure email doesn't already exist."""
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        if TemporaryUser.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "You already have an account. Please activate it."})
        return attrs


class ResendActivationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        help_text="Enter the email address associated with your account."
    )

    class Meta:
        fields = ("email",)

    def validate_email(self, value):
        """Ensure email is associated with a user."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "This email already activated"
            )
        if not TemporaryUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "No user is associated with this email address"
            )
        return value
