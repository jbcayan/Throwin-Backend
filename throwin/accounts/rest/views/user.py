"""Views for user"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from drf_spectacular.utils import extend_schema

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from accounts.choices import UserKind
from accounts.models import TemporaryUser, Like
from accounts.rest.serializers.user import (
    EmailChangeRequestSerializer,
    UserNameSerializer,
    StuffDetailForConsumerSerializer, MeSerializer,
)

from common.permissions import (
    IsConsumerUser,
    CheckAnyPermission, IsConsumerOrGuestUser, IsAdminUser, IsRestaurantStuffUser, IsSuperAdminUser,
)

User = get_user_model()


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
                "detail": "User Activated Successfully"
            }, status=status.HTTP_200_OK)

        except Exception:
            return Response({
                "detail": "Invalid Token or User"
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Set name for existing user",
    request=UserNameSerializer
)
class SetUserName(generics.GenericAPIView):
    """View for set name for existing user"""

    available_permission_classes = (
        IsConsumerUser,
    )
    permission_classes = (CheckAnyPermission,)
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
    """Endpoint to verify and change the user's email."""
    available_permission_classes = (
        IsConsumerUser,
        IsAdminUser,
        IsSuperAdminUser,
    )
    permission_classes = (CheckAnyPermission,)

    def post(self, request, token=None):

        if not token:
            return Response(
                {"detail": "Token is missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            access_token = AccessToken(token)
            user_id = access_token.get("user_id")
            new_email = access_token.get("new_email")

            if not (request.user.is_authenticated and request.user.id == user_id):
                return Response(
                    {"detail": "Requested user does not match the authenticated user"},
                    status=status.HTTP_403_FORBIDDEN
                )

            request.user.email = new_email
            request.user.is_verified = True
            request.user.save(update_fields=["email", "is_verified"])

            return Response(
                {"detail": "Email changed successfully"},
                status=status.HTTP_200_OK
            )

        except AccessToken.DoesNotExist:
            return Response(
                {"detail": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    summary="Get restaurant stuff details for consumer",
    description="Get restaurant stuff details for consumer",
    request=StuffDetailForConsumerSerializer
)
class StuffDetailForConsumer(generics.RetrieveAPIView):
    available_permission_classes = (
        IsConsumerOrGuestUser,
        IsConsumerUser,
        IsAdminUser,
        IsRestaurantStuffUser,
        IsSuperAdminUser
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = StuffDetailForConsumerSerializer

    def get_object(self):
        return User().get_all_actives().get(username=self.kwargs["username"])


class ConsumerLikeStuffCreateDestroy(generics.GenericAPIView):

    def post(self, request, *args, **kwargs):
        stuff_uid = str(self.kwargs.get("uid", None))
        stuff_id = get_object_or_404(
            User,
            uid=stuff_uid,
            is_active=True,
            kind=UserKind.RESTAURANT_STUFF
        ).id

        if self.request.user.is_authenticated:
            like, created = Like.objects.get_or_create(
                consumer=self.request.user,
                staff_id=stuff_id
            )
            if created:
                return Response({
                    "detail": "Stuff member Liked"
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "detail": "Stuff member already Liked"
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Add a session for guest user
            liked_stuff_uids = request.session.get("liked_stuff_uids", [])
            if stuff_uid not in liked_stuff_uids:
                liked_stuff_uids.append(stuff_uid)
                request.session["liked_stuff_uids"] = liked_stuff_uids
                return Response({
                    "detail": "Stuff member Liked"
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "detail": "Stuff member already Liked"
                }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        stuff_uid = str(self.kwargs.get("uid", None))
        stuff_id = get_object_or_404(
            User,
            uid=stuff_uid,
            is_active=True,
            kind=UserKind.RESTAURANT_STUFF
        ).id

        if self.request.user.is_authenticated:
            Like.objects.filter(
                consumer=self.request.user,
                stuff_id=stuff_id
            ).delete()
            return Response({
                "detail": "Stuff member Unliked"
            }, status=status.HTTP_204_NO_CONTENT)
        else:
            liked_stuff_uids = request.session.get("liked_stuff_uids", [])
            if stuff_uid in liked_stuff_uids:
                liked_stuff_uids.remove(stuff_uid)
                request.session["liked_stuff_uids"] = liked_stuff_uids
                return Response({
                    "detail": "Stuff member Unliked"
                }, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({
                    "detail": "Stuff member already Unliked"
                }, status=status.HTTP_400_BAD_REQUEST)


class FavoriteStuffList(generics.ListAPIView):
    """
    API endpoint to list all favorite (liked) stuff members for the authenticated consumer.
    """
    serializer_class = StuffDetailForConsumerSerializer
    available_permission_classes = (
        IsConsumerOrGuestUser,
        IsConsumerUser,
    )

    def get_queryset(self):
        consumer = self.request.user
        # Ensures only "liked" staff by this consumer are included in the queryset
        liked_staff_ids = Like.objects.filter(consumer=consumer).values_list("staff", flat=True)
        return User.objects.filter(id__in=liked_staff_ids, kind=UserKind.RESTAURANT_STUFF)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema(
    summary="Get user details",
    description="Get user details",
    request=MeSerializer
)
class Me(generics.GenericAPIView):
    serializer_class = MeSerializer
    available_permission_classes = (
        IsConsumerUser,
        IsConsumerOrGuestUser,
        IsAdminUser,
        IsRestaurantStuffUser,
        IsSuperAdminUser
    )
    permission_classes = (CheckAnyPermission,)

    def get_object(self):
        if self.request.user.is_authenticated:
            # Fetch the user with the related UserProfile to avoid additional queries
            return User.objects.select_related('profile').get(id=self.request.user.id)
        else:
            return None  # This will trigger a response in the `get` method for guests

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user = self.get_object()
            return Response(self.serializer_class(user).data)
        else:
            guest_name = request.session.get("guest_name", "Anonymous user")
            return Response({
                "name": guest_name
            }, status=status.HTTP_200_OK)
