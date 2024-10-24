"""Write custom permisssion for consumer, restaurant stuff and admin."""

from rest_framework.permissions import BasePermission

from accounts.choices import UserKind
from store.choices import StoreUserRole


class IsConsumerUser(BasePermission):
    """Permission for consumer"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            return request.user.kind == UserKind.CONSUMER
        except Exception:
            return False
    