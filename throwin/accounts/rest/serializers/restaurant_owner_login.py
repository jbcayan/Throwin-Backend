from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

from accounts.choices import UserKind

User = get_user_model()


class RestaurantOwnerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError({
                "detail": "Must include email and password."
            }, code="authorization")

        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )

        if user:
            if user.kind != UserKind.RESTAURANT_OWNER:
                raise serializers.ValidationError(
                    {"detail": "User is not a restaurant owner."
                     }, code="authorization"
                )
            if not user.is_verified:
                raise serializers.ValidationError(
                    {"detail": "User is not verified."
                     }, code="authorization"
                )

        if not user:
            raise serializers.ValidationError(
                {"detail": "Unable to log in with provided credentials."
                 }, code="authorization"
            )
        attrs["user"] = user
        return attrs
