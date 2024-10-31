"""Serializers for User model."""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from accounts.choices import UserKind
from accounts.models import TemporaryUser

User = get_user_model()


class UserRegisterSerializerWithEmail(serializers.ModelSerializer):
    """Serializer for user registration with email."""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
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
