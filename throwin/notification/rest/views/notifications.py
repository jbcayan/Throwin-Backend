"""Views for notifications."""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from notification.models import Notification
from notification.rest.serializers.notifications import (
    NotificationListSerializer
)
from common.permissions import IsAdminUser, IsSuperAdminUser, IsConsumerUser, CheckAnyPermission, IsConsumerOrGuestUser

from common.choices import Status

from django.db.models import Q, Case, When, Value, BooleanField


class NotificationList(generics.ListCreateAPIView):
    """List all notifications."""
    serializer_class = NotificationListSerializer

    def get_permissions(self):
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

    def get_queryset(self):
        user = self.request.user
        session_key = self.request.session.session_key

        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key

        user_key = str(user.id) if user.is_authenticated else session_key

        return Notification.objects.filter(status=Status.ACTIVE).annotate(
            is_read=Case(
                When(Q(read_by__has_key=user_key), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
