"""Views for user"""

from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import AccessToken

from accounts.rest.serializers.user import (
    EmailChangeRequestSerializer,
    UserNameSerializer

)
from accounts.utils import email_activation_token

from common.permissions import IsConsumerUser

User = get_user_model()


@extend_schema(request=UserNameSerializer)
class UserName(generics.CreateAPIView):
    """View for set name for existing user"""

    permission_classes = [IsConsumerUser]
    serializer_class = UserNameSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "detail": "User Name Updated Successfully",
        }, status=status.HTTP_200_OK,
        )


@extend_schema()
class AccountActivation(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            if email_activation_token.check_token(user, token):
                user.is_active = True
                user.is_verified = True
                user.save()
                return Response({
                    "detail": "Account Activated Successfully"
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "detail": "Invalid Token"
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({
                "detail": "Invalid Token or User"
            }, status=status.HTTP_400_BAD_REQUEST)


class EmailChangeRequest(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmailChangeRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response({
            "detail": "Validation email Sent to your new email"
        }, status=status.HTTP_200_OK)


@extend_schema()
class VerifyEmailChange(APIView):
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
