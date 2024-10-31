"""Views for user"""
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import AccessToken

from accounts.choices import UserKind
from accounts.models import TemporaryUser

from accounts.rest.serializers.user import (
    EmailChangeRequestSerializer,
    UserNameSerializer, StuffDetailForConsumerSerializer,
)
from accounts.utils import email_activation_token

from common.permissions import IsConsumerUser

User = get_user_model()


@extend_schema(
    summary="Set name for existing user",
    request=UserNameSerializer
)
class SetUserName(generics.GenericAPIView):
    """View for set name for existing user"""

    permission_classes = [IsConsumerUser]
    serializer_class = UserNameSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "detail": "User Name Updated Successfully",
        }, status=status.HTTP_200_OK,
        )


@extend_schema(
    summary="Activate User Account using URL Path Parameters",
    description="Activate User Account using URL Path Parameters",
)
class AccountActivation(generics.GenericAPIView):
    """View for activate user account"""

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            temp_user = TemporaryUser.objects.get(pk=uid, token=token)

            TOKEN_EXPIRATION_HOURS = 48  # Token validity period

            # check if token is expired
            if (
                    temp_user.created_at + timedelta(hours=TOKEN_EXPIRATION_HOURS)
                    <= timezone.now()
            ):
                return Response({
                    "detail": "Token Expired"
                }, status=status.HTTP_400_BAD_REQUEST)

            # if not expired, create user
            user = User.objects.create_user(
                email=temp_user.email,
                kind=temp_user.kind,
                is_verified=True
            )
            user.set_password(temp_user.password)
            user.save()

            # delete temp user
            temp_user.delete()

            return Response({
                "detail": "Account Activated Successfully"
            }, status=status.HTTP_200_OK)

        except Exception:
            return Response({
                "detail": "Invalid Token or User"
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Request for email change",
    description="Request for email change",
    request=EmailChangeRequestSerializer
)
class EmailChangeRequest(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmailChangeRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response({
            "detail": "Validation email Sent to your new email"
        }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Verify and change user email",
    description=(
            "Provide the token as a query parameter to verify and update the user's email.\n\n"
            "**Example Request:**\n"
            "`GET /api/v1/auth/email-change/verify/?token=<your_token>`\n\n"
            "The token should be sent as a query parameter in the URL. This token contains the user's "
            "ID and new email address, and it must be valid and not expired."
    ),
)
class VerifyEmailChange(generics.GenericAPIView):
    def get(self, request):
        token = request.query_params.get("token", "")

        if not token:
            return Response({
                "detail": "Token is missing"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            new_email = access_token["new_email"]

            user = User.objects.get(id=user_id)
            user.email = new_email  # Update the user's email
            user.is_verified = True
            user.save()

            return Response({
                "detail": "Email Changed Successfully"
            }, status=status.HTTP_200_OK)

        except Exception:
            return Response({
                "detail": "Invalid Token or Expired"
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Get user details for consumer",
    description="Get user details for consumer",
    request=StuffDetailForConsumerSerializer
)
class StuffDetailForConsumer(generics.RetrieveAPIView):
    permission_classes = [IsConsumerUser]
    serializer_class = StuffDetailForConsumerSerializer

    def get_object(self):
        return User().get_all_actives().get(uid=self.kwargs["uid"])
