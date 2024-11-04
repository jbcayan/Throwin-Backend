"""Serializer for user"""

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers

from accounts.choices import UserKind
from accounts.models import Like
from accounts.tasks import send_mail_task
from accounts.utils import generate_verification_token

from versatileimagefield.serializers import VersatileImageFieldSerializer

from common.serializers import BaseSerializer

User = get_user_model()


class UserNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name",)

    def create(self, validated_data):
        """Set name for existing user"""
        name = validated_data["name"]
        if User.objects.filter(name=name).exists():
            raise serializers.ValidationError("Name is already in use")

        user = self.context["request"].user
        user.name = name
        user.save()
        return user


class EmailChangeRequestSerializer(serializers.Serializer):
    new_email = serializers.EmailField()

    def validate_new_email(self, value):
        """Ensure that new email is not already in use"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use")
        return value

    def save(self, user):
        new_email = self.validated_data["new_email"]

        # generate token for email verification
        token = generate_verification_token(user, new_email)

        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"

        # Send a verification email to the new email address
        send_mail_task(
            subject="Verify Email",
            message=f"Please click the link below to verify your email. {verification_url}",
            to_email=new_email,
        )


class StuffDetailForConsumerSerializer(BaseSerializer):
    """Serializer to represent restaurant stuff details."""

    introduction = serializers.CharField(
        source="profile.introduction",
        allow_blank=True,
        allow_null=True,
    )
    score = serializers.IntegerField(
        source="profile.total_score",
        default=0
    )
    image = VersatileImageFieldSerializer(
        sizes='profile_image'
    )

    class Meta(BaseSerializer.Meta):
        model = User
        fields = ("uid", "name", "introduction", "score", "image")


# class ConsumerLikeStuffSerializer(serializers.Serializer):
#     """Serializer to handle liking/unliking stuff."""
#
#     stuff_uid = serializers.UUIDField(
#         required=True
#     )
#
#     def validate_stuff_uid(self, value):
#         """Check that the stuff exists and is of the right kind."""
#
#         try:
#             stuff = User.objects.get(uid=value, kind=UserKind.RESTAURANT_STUFF)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("Stuff does not exist")
#
#         return value
#
#     def create(self, validated_data):
#         """Create a new like for authenticated user and add a session for guest users."""
#
#         request = self.context.get("request")
#         stuff_uid = validated_data["stuff_uid"]
#
#         if request and request.user.is_authenticated:
#             # Create a new like
#             like, created = Like.objects.get_or_create(
#                 consumer=request.user.id,
#                 staff__uid=stuff_uid
#             )
#             return {"detail": "stuff member liked"} if created else {"detail": "Stuff member already liked"}
#         else:
#             # Add a session for guest users
#             liked_stuff_uids = request.session.get("liked_stuff_uids", [])
#             print("liked_stuff_uids", liked_stuff_uids)
#             if stuff_uid not in liked_stuff_uids:
#                 liked_stuff_uids.append(stuff_uid)
#                 request.session["liked_stuff_uids"] = liked_stuff_uids
#                 print("added to session", request.session["liked_stuff_uids"])
#                 request.session.modified = True
#                 return {"detail": "stuff member liked for the guest user"}
#             else:
#                 return {"detail": "Stuff member already liked"}
#
#
#     def delete(self, validated_data):
#         """Delete a like for authenticated user and remove a session for guest users."""
#
#         request = self.context.get("request")
#         stuff_uid = validated_data["stuff_uid"]
#
#         if request and request.user.is_authenticated:
#             # Delete a like
#             Like.objects.filter(
#                 consumer=request.user.id,
#                 staff__uid=stuff_uid
#             ).delete()
#             return {"detail": "stuff member unliked"}
#         else:
#             # unlike for gust users, using a session
#             liked_stuff_uids = request.session.get("liked_stuff_uids", [])
#             if stuff_uid in liked_stuff_uids:
#                 liked_stuff_uids.remove(stuff_uid)
#                 request.session["liked_stuff_uids"] = liked_stuff_uids
#                 request.session.modified = True
#                 return {"detail": "stuff member unliked for the guest user"}
#             else:
#                 return {"detail": "Stuff member already unliked"}
