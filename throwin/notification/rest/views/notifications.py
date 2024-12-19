"""Views for notifications."""
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from notification.models import Notification
from notification.rest.serializers.notifications import (
    NotificationListSerializer,
    NotificationDetailSerializer,
    NotificationDetailAdminSerializer,
)
from common.permissions import (
    IsAdminUser,
    IsSuperAdminUser,
    IsConsumerUser,
    CheckAnyPermission,
    IsConsumerOrGuestUser
)
from common.choices import Status

from django.db.models import Q, Case, When, Value, BooleanField


class NotificationList(generics.ListCreateAPIView):
    """List all notifications."""

    def get_permissions(self):
        # Set different permission classes based on the HTTP method
        if self.request.method == 'GET':
            self.available_permission_classes = (
                IsAdminUser,
                IsSuperAdminUser,
                IsConsumerUser,
                IsConsumerOrGuestUser,
            )
        else:
            self.available_permission_classes = (
                IsAdminUser,
                IsSuperAdminUser,
            )
        self.permission_classes = (CheckAnyPermission,)
        return super().get_permissions()

    def get_serializer_class(self):
        # Set different serializer classes based on the HTTP method
        if self.request.method == 'POST':
            return NotificationDetailAdminSerializer
        else:
            return NotificationListSerializer

    def get_queryset(self):
        # Get all active notifications and annotate is_read
        if self.request.user.is_authenticated:
            user_id_str = str(self.request.user.id)  # Cast user ID to string
            return Notification.objects.filter(status=Status.ACTIVE).annotate(
                is_read=Case(
                    When(Q(read_by__has_key=user_id_str), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
        else:
            # If user is not authenticated, return all active notifications with is_read set to False
            return Notification().get_all_actives().annotate(
                is_read=Value(False)
            )


class NotificationDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a notification."""

    def get_permissions(self):
        # Set different permission classes based on the HTTP method
        if self.request.method == 'GET':
            self.available_permission_classes = (
                IsAdminUser,
                IsSuperAdminUser,
                IsConsumerUser,
                IsConsumerOrGuestUser,
            )
        else:
            self.available_permission_classes = (
                IsAdminUser,
                IsSuperAdminUser,
            )
        self.permission_classes = (CheckAnyPermission,)
        return super().get_permissions()

    def get_serializer_class(self):
        # Set different serializer classes based on the HTTP method
        if self.request.method == 'GET':
            return NotificationDetailSerializer
        else:
            return NotificationDetailAdminSerializer

    def get_object(self, *args, **kwargs):
        # Retrieve the notification by UID
        uid = self.kwargs.get('uid')
        return get_object_or_404(
            Notification,
            uid=uid
        )
