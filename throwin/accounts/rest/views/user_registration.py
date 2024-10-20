"""Views for user registration"""
from rest_framework.response import Response
from accounts.rest.serializers.user_registration import UserRegisterSerializerWithEmail
from rest_framework import generics, status
from drf_spectacular.utils import extend_schema


@extend_schema(tags=["User Registration"])
class UserRegistration(generics.CreateAPIView):
    """View for user registration"""

    serializer_class = UserRegisterSerializerWithEmail

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "detail": "User Created Successfully",
            },
            status=status.HTTP_201_CREATED,
        )
