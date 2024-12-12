from django.db import models
from django.db.models import JSONField
from django.shortcuts import get_object_or_404

from common.models import BaseModel


# Create your models here.
class Notification(BaseModel):
    title = models.CharField(max_length=255)
    body = models.TextField()
    read_by = JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Tracks read status by user ID or session ID"
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

    def mark_as_read(self, user_key):
        """
            Marks the notification as read for a given user or session.
        """
        self.read_by[user_key] = True
        self.save()

    def is_read(self, user_key):
        """
            Checks if the notification has been read by a given user or session.
        """
        return self.read_by.get(user_key, False)

    @classmethod
    def get_notification(cls, notification_uid):
        """
        Fetches a notification object by UID or raises a 404 error.
        """
        return get_object_or_404(cls, uid=notification_uid)
