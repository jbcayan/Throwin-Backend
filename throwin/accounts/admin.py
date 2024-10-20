"""Django Admin Configuration"""

from django.contrib import admin
from accounts.models import User, UserProfile, Like
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserProfileInline(admin.StackedInline):
    """User Profile Inline for User Admin."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    readonly_fields = ["total_score"]  # Total score is not editable

    def get_queryset(self, request):
        """Only show profiles for users who have them."""
        queryset = super().get_queryset(request)
        return queryset.select_related("user")

    def has_change_permission(self, request, obj=None):
        """Only allow editing profiles for staff users."""
        return bool(obj and obj.kind == "restaurant_stuff")


class UserAdmin(BaseUserAdmin):
    """User Admin Configuration"""

    ordering = ["-id"]
    list_display = ["email", "phone_number", "name", "kind", "is_active", "is_staff", "is_superuser"]
    fieldsets = (
        (None, {"fields": ("email", "phone_number", "name", "gender", "kind", "image")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ["last_login", "date_joined"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "phone_number", "password1", "password2"),
            },
        ),
    )

    def get_inlines(self, request, obj=None):
        """Add profile inline only if the user is restaurant staff."""
        return [UserProfileInline] if obj and obj.kind == "restaurant_stuff" else []


admin.site.register(User, UserAdmin)


class LikeAdmin(admin.ModelAdmin):
    """Admin configuration for Likes."""
    list_display = ["consumer", "staff", "created_at"]
    search_fields = ["consumer__name", "staff__name"]
    list_filter = ["consumer__kind", "staff__kind"]
    ordering = ["-created_at"]


admin.site.register(Like, LikeAdmin)
