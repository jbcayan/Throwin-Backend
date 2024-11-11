"""Django Admin Configuration"""

from django.contrib import admin

from accounts.models import User, UserProfile, Like, TemporaryUser

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
        """Allow editing profiles for all users, if staffed."""
        return bool(request.user.is_staff)


class UserAdmin(BaseUserAdmin):
    """User Admin Configuration"""
    list_display = [
        "id", "uid", "email", "phone_number", "name", "username",
        "kind", "is_active", "is_staff", "is_superuser"
    ]

    list_filter = ["kind", "is_active", "is_staff", "is_superuser"]

    fieldsets = (
        (None,
         {
             "fields":
                 (
                     "status",
                     "email",
                     "phone_number",
                     "name",
                     "username",
                     "kind",
                     "gender",
                     "image",
                     "auth_provider",
                     "store",
                 )
         }
         ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_verified",
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
        """Add profile inline for every user, regardless of kind."""
        return [UserProfileInline]


admin.site.register(User, UserAdmin)


class LikeAdmin(admin.ModelAdmin):
    """Admin configuration for Likes."""
    list_display = ["consumer", "staff", "created_at"]
    search_fields = ["consumer__name", "staff__name"]
    ordering = ["-created_at"]


admin.site.register(Like, LikeAdmin)


class TemporaryUserAdmin(admin.ModelAdmin):
    """Admin configuration for TemporaryUser."""
    list_display = ["id", "email", "token", "created_at"]
    search_fields = ["email", "token"]
    ordering = ["-created_at"]


admin.site.register(TemporaryUser, TemporaryUserAdmin)
