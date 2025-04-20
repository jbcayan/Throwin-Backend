"""Views for user"""

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.choices import UserKind
from accounts.filters import UserFilter
from accounts.models import Like
from accounts.rest.serializers.user import (
    EmailChangeRequestSerializer,
    UserNameSerializer,
    StaffDetailForConsumerSerializer,
    MeSerializer,
    GuestNameSerializer,
    AccountActivationSerializer,
    EmailChangeTokenSerializer,
    StaffLikeToggleSerializer,
    GetRestaurantOwnerReplySerializer,
)
from common.permissions import (
    IsConsumerUser,
    CheckAnyPermission,
    IsConsumerOrGuestUser,
    IsGlowAdminUser,
    IsRestaurantStaffUser,
    IsFCAdminUser,
    IsSuperAdminUser,
    IsRestaurantOwnerUser, IsSalesAgentUser,
)
from review.models import Reply
from store.models import StoreUser
from store.rest.serializers.store_stuff import (
    StoreStuffListSerializer,
    StoreUserSerializer
)

User = get_user_model()


@extend_schema(
    summary="Activate User Account using URL Path Parameters",
    description="Activate User Account using URL Path Parameters",
)
class AccountActivation(generics.GenericAPIView):
    """View for activating user account"""
    serializer_class = AccountActivationSerializer

    def get(self, request, uidb64, token):
        serializer = self.get_serializer(data={'uidb64': uidb64, 'token': token})
        serializer.is_valid(raise_exception=True)

        temp_user = serializer.validated_data['temp_user']

        # Create user
        user = User.objects.create_user(
            email=temp_user.email,
            kind=temp_user.kind,
            is_verified=True
        )
        user.set_password(temp_user.password)
        user.save()

        # Delete temp user
        temp_user.delete()

        return Response({
            "detail": "User Activated Successfully"
        }, status=status.HTTP_200_OK)


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
            "detail": "User Name Updated Successfully"
             }, status=status.HTTP_200_OK,
        )


@extend_schema(
    summary="Set name for guest user using session",
)
class SetGuestName(generics.GenericAPIView):
    """View for set name for guest user"""

    available_permission_classes = (
        IsConsumerOrGuestUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = GuestNameSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract the name from the validated data
        name = serializer.validated_data.get("name", "").strip()

        # Set "Anonymous user" if name is empty or blank
        if not name:
            request.session["guest_name"] = "Anonymous user"
        else:
            request.session["guest_name"] = name

        return Response(
            {"detail": "Guest Name Updated Successfully"},
            status=status.HTTP_200_OK
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
            "Provide the token in the url path to verify and update the user's email.\n\n"
            "**Example Request:**\n"
            "`GET /auth/users/email-change-request/verify/<your_token>`\n\n"
    ),
)
class EmailChangeRequestVerify(generics.GenericAPIView):
    """Endpoint to verify and change the user's email."""
    serializer_class = EmailChangeTokenSerializer

    available_permission_classes = (
        IsConsumerUser,
        IsGlowAdminUser,
        IsFCAdminUser,
    )
    permission_classes = (CheckAnyPermission,)

    def post(self, request, token=None):
        if not token:
            return Response(
                {"detail": "Token is missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data={'token': token})
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']
        new_email = serializer.validated_data['new_email']

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


@extend_schema(
    summary="Get restaurant staff details for consumer",
    description="Get restaurant staff details for consumer",
    request=StaffDetailForConsumerSerializer
)
class StaffDetailForConsumer(generics.RetrieveAPIView):
    available_permission_classes = (
        IsConsumerOrGuestUser,
        IsConsumerUser,
        IsGlowAdminUser,
        IsRestaurantStaffUser,
        IsFCAdminUser,
        IsSuperAdminUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = StaffDetailForConsumerSerializer

    def get_object(self):
        return User().get_all_actives().get(username=self.kwargs["username"])

    def get(self, request, *args, **kwargs):

        # get store code from url
        store_code = self.kwargs.get("store_code", None)

        # Retrieve the staff
        try:
            staff = self.get_object()
            store_user = StoreUser.objects.get(
                store__code=store_code,
                user_id=staff.id,
                role=UserKind.RESTAURANT_STAFF
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "Staff member not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Serialize the staff
        serializer = self.serializer_class(staff)
        data = serializer.data

        # Add Liked field
        liked = False
        if request.user.is_authenticated:
            # Add is_liked field for authenticated consumer
            liked = Like.objects.filter(
                consumer=request.user,
                staff_id=staff.id
            ).exists()
        else:
            # Add a session for guest user
            liked = request.session.get("liked_staff_uids", []).count(staff.uid) > 0

        data["liked"] = liked
        data["store_uid"] = store_user.store.uid
        data["store_name"] = store_user.store.name
        data["restaurant_uid"] = store_user.store.restaurant.uid

        return Response(data, status=status.HTTP_200_OK)


class ConsumerLikeStaffToggle(generics.GenericAPIView):
    """
    Toggle 'like' status for a staff member by the consumer.
    """
    serializer_class = StaffLikeToggleSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={'uid': self.kwargs.get("uid")})
        serializer.is_valid(raise_exception=True)
        staff = serializer.validated_data['uid']

        if self.request.user.is_authenticated:
            # For authenticated users
            like, created = Like.objects.get_or_create(
                consumer=self.request.user,
                staff=staff
            )
            if created:
                message = "Staff member Liked"
                status_code = status.HTTP_201_CREATED
            else:
                like.delete()
                message = "Staff member Unliked"
                status_code = status.HTTP_200_OK
        else:
            # For guest users
            if not request.session.session_key:
                request.session.create()  # Ensure session is initialized

            liked_staff_uids = request.session.get("liked_staff_uids", [])
            staff_uid = str(staff.uid)
            if staff_uid in liked_staff_uids:
                liked_staff_uids.remove(staff_uid)
                message = "Staff member Unliked"
                status_code = status.HTTP_200_OK
            else:
                liked_staff_uids.append(staff_uid)
                message = "Staff member Liked"
                status_code = status.HTTP_201_CREATED

            # Update session
            request.session["liked_staff_uids"] = liked_staff_uids

        return Response({
            "detail": message
        }, status=status_code)


class FavoriteStaffList(generics.ListAPIView):
    """
    API endpoint to list all favorite (liked) staff members for the authenticated consumer.
    """
    serializer_class = StaffDetailForConsumerSerializer
    available_permission_classes = (
        IsConsumerOrGuestUser,
        IsConsumerUser,
        IsGlowAdminUser,
        IsFCAdminUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_queryset(self):
        consumer = self.request.user

        if consumer.is_authenticated:
            # Get liked staff for authenticated consumer
            liked_staff_ids = Like.objects.filter(consumer=consumer).values_list("staff", flat=True)
        else:
            # Get liked staff for guest
            liked_staff_uids = self.request.session.get("liked_staff_uids", [])
            liked_staff_ids = User.objects.filter(
                uid__in=liked_staff_uids,
                kind=UserKind.RESTAURANT_STAFF
            ).values_list("id", flat=True)
            return User.objects.filter(id__in=liked_staff_ids)

        return User.objects.filter(id__in=liked_staff_ids, kind=UserKind.RESTAURANT_STAFF)

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
        IsGlowAdminUser,
        IsRestaurantStaffUser,
        IsFCAdminUser,
        IsSalesAgentUser,
        IsRestaurantOwnerUser,
        IsSuperAdminUser,
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


@extend_schema(
    summary="Account deletion for registered users",
    description="Account deletion for registered users",
)
class DeleteUser(generics.DestroyAPIView):
    available_permission_classes = (
        IsGlowAdminUser,
        IsFCAdminUser,
        IsConsumerUser
    )
    permission_classes = (CheckAnyPermission,)

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StaffList(generics.ListAPIView):
    """
    API endpoint to list all staff members for the authenticated consumer.
    """
    serializer_class = StoreStuffListSerializer
    available_permission_classes = (
        IsConsumerOrGuestUser,
        IsConsumerUser,
        IsGlowAdminUser,
        IsFCAdminUser,
        IsRestaurantStaffUser,
        IsRestaurantOwnerUser,
        IsSuperAdminUser,
    )
    permission_classes = (CheckAnyPermission,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter

    def get_queryset(self):
        return User().get_all_actives().filter(kind=UserKind.RESTAURANT_STAFF)


@extend_schema(
    summary="Get store stuff list by staff name {param request}",
    description="Request example: /auth/users/store-user-search?name=Test Staff",
    request=StoreStuffListSerializer
)
class StoreUserSearchView(generics.GenericAPIView):
    """
    API to search for users by name and retrieve their store associations.
    """
    serializer_class = StoreUserSerializer

    def get(self, request, *args, **kwargs):
        name = self.request.query_params.get("name", None)

        if not name:
            return Response(
                {"detail": "Name is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filter StoreUser objects by user__name
        store_users = StoreUser.objects.filter(
            user__name__icontains=name,
            role=UserKind.RESTAURANT_STAFF
        ).select_related(
            "user", "store", "store__restaurant"
        )

        if not store_users.exists():
            return Response(
                {"detail": "No users found with the given name."},
                status=status.HTTP_404_NOT_FOUND
            )

        data = self.serializer_class(store_users, many=True).data
        return Response(data, status=status.HTTP_200_OK)

@extend_schema(
    summary="Get replies made by restaurant owners on reviews that belong to the authenticated consumer.",
    description="Get replies made by restaurant owners on reviews that belong to the authenticated consumer.",
    request=GetRestaurantOwnerReplySerializer
)
class ConsumerRestaurantOwnerRepliesAPIView(generics.ListAPIView):
    """
    API endpoint that returns replies made by restaurant owners on reviews
    that belong to the authenticated consumer.
    """
    available_permission_classes = (
        IsConsumerUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = GetRestaurantOwnerReplySerializer

    def get_queryset(self):
        user = self.request.user
        # Filter replies where:
        # - attached review's consumer is the current user
        # - reply has a non-null restaurant_owner
        return Reply.objects.filter(
            review__consumer=user,
            restaurant_owner__isnull=False
        )

@extend_schema(
    summary="Get detailed information of a single reply made by a restaurant owner on a review that belongs to the authenticated consumer.",
    description="Get detailed information of a single reply made by a restaurant owner on a review that belongs to the authenticated consumer.",
    request=GetRestaurantOwnerReplySerializer
)
class ConsumerRestaurantOwnerReplyDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint that retrieves detailed information of a single reply made by a
    restaurant owner on a review that belongs to the authenticated consumer.
    """
    available_permission_classes = (
        IsConsumerUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = GetRestaurantOwnerReplySerializer
    lookup_field = 'uid'

    def get_queryset(self):
        user = self.request.user
        # Filter to make sure the reply belongs to a review of the consumer
        # and that it was made by a restaurant owner.
        return Reply.objects.filter(
            review__consumer=user,
            restaurant_owner__isnull=False
        )