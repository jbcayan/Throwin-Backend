"""Django Admin Configuration"""

from django.contrib import admin
from accounts.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


# Register your models here.
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


admin.site.register(User, UserAdmin)