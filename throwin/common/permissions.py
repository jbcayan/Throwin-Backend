"""Write custom permission for consumer, restaurant stuff and admin."""

from rest_framework.permissions import BasePermission

from accounts.choices import UserKind
from store.choices import StoreUserRole


class IsConsumerUser(BasePermission):
    """Permission for consumer"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.is_verified:
            return False
        try:
            return request.user.kind == UserKind.CONSUMER
        except Exception:
            return False


class IsConsumerOrGuestUser(BasePermission):
    """Permission for consumer and guest user"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return True
        if not request.user.is_verified:
            return True
        try:
            return request.user.kind in [UserKind.CONSUMER, UserKind.UNDEFINED]
        except Exception:
            return True


class IsGlowAdminUser(BasePermission):
    """Permission for admin"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.is_verified:
            return False
        try:
            return request.user.kind == UserKind.GLOW_ADMIN
        except Exception:
            return False


class IsFCAdminUser(BasePermission):
    """Permission for admin"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.is_verified:
            return False
        try:
            return request.user.kind == UserKind.FC_ADMIN
        except Exception:
            return False

class IsSalesAgentUser(BasePermission):
    """Permission for admin"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.is_verified:
            return False
        try:
            return request.user.kind == UserKind.SALES_AGENT
        except Exception:
            return False


class IsRestaurantOwnerUser(BasePermission):
    """Permission for restaurant owner"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.is_verified:
            return False
        try:
            return request.user.kind == UserKind.RESTAURANT_OWNER
        except Exception:
            return False


class IsSuperAdminUser(BasePermission):
    """Permission for super admin"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.is_verified:
            return False
        try:
            return request.user.kind == UserKind.SUPER_ADMIN
        except Exception:
            return False


class IsRestaurantStaffUser(BasePermission):
    """Permission for restaurant stuff"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.is_verified:
            return False
        try:
            return request.user.kind == UserKind.RESTAURANT_STAFF
        except Exception:
            return False


class CheckAnyPermission(BasePermission):
    """
    Custom permission to check if any of the permissions in `available_permission_classes` are met.
    """

    def has_permission(self, request, view):

        for permission_class in getattr(view, "available_permission_classes", []):
            if permission_class().has_permission(request, view):
                return True

        return False
