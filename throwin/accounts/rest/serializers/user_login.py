from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

User = get_user_model()


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(request=self.context.get("request"), email=email, password=password)

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                raise serializers.ValidationError(
                    {"msg": "Unable to log in with provided credentials."
                     }, code="authorization"
                )
        else:
            raise serializers.ValidationError({
                "msg": "Must include email and password."
            }, code="authorization")

        attrs["user"] = user
        return attrs
