"""Django Admin Configuration"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import User, UserProfile, Like, TemporaryUser


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    fk_name = "user"
    extra = 0
    can_delete = False
    verbose_name_plural = "Profile"
    readonly_fields = ["total_score"]

    def get_queryset(self, request):
        """Optimize query to include related user information."""
        queryset = super().get_queryset(request)
        return queryset.select_related("user")


class UserAdmin(BaseUserAdmin):
    """Custom admin for User model."""
    list_display = [
        "email", "id", "uid", "phone_number", "name", "username",
        "kind", "is_active", "is_staff", "is_superuser"
    ]
    search_fields = ["email", "phone_number", "uid", "id", "name", "username"]
    list_filter = ["kind", "is_active", "is_staff", "is_superuser"]
    ordering = ["-id"]

    fieldsets = (
        (None, {
            "fields": (
                "status",
                "email",
                "phone_number",
                "name",
                "username",
                "kind",
                "gender",
                "image",
                "auth_provider",
                "password"
            )
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_verified",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ["last_login", "date_joined"]

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone_number", "password1", "password2"),
        }),
    )

    def get_inlines(self, request, obj=None):
        """Include UserProfile inline for all users."""
        return [UserProfileInline]


class LikeAdmin(admin.ModelAdmin):
    """Custom admin for Like model."""
    list_display = ["consumer", "staff", "created_at"]
    search_fields = ["consumer__name", "staff__name", "consumer__email", "staff__email"]
    list_filter = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        """Optimize query for Like model."""
        queryset = super().get_queryset(request)
        return queryset.select_related("consumer", "staff")


class TemporaryUserAdmin(admin.ModelAdmin):
    """Custom admin for TemporaryUser model."""
    list_display = ["email", "id", "uid", "token", "kind", "created_at"]
    search_fields = ["email", "token"]
    list_filter = ["kind", "created_at"]
    ordering = ["-created_at"]


# Register models to admin
admin.site.register(User, UserAdmin)
admin.site.register(Like, LikeAdmin)
admin.site.register(TemporaryUser, TemporaryUserAdmin)
