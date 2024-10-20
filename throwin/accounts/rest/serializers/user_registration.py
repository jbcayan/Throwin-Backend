"""Serializers for User model."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.choices import UserKind

User = get_user_model()


class UserRegisterSerializerWithEmail(serializers.ModelSerializer):
    """Serializer for user registration with email."""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
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

        # Create a new user with email and password
        user = User.objects.create_user(
            email=validated_data["email"],
            kind=UserKind.CONSUMER,
        )
        user.set_password(validated_data["password"])
        user.save()

        return user
