from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
    PermissionsMixin
)
from django.db import models
from django.db.models.signals import post_save

from versatileimagefield.fields import VersatileImageField

from accounts.choices import GenderChoices, UserKind, AuthProvider
from accounts.signals import post_save_user

from common.models import BaseModel

from core.utils import get_user_media_file_prefix


# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        """Create a regular user with either email or phone number"""
        if not email and not phone_number:
            raise ValueError("User must have either email or phone number")
        user = self.model(
            email=self.normalize_email(email),
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, phone_number=None, password=None, **extra_fields):
        """Create a superuser"""
        user = self.create_user(email, phone_number, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.kind = UserKind.ADMIN
        user.save(using=self._db)
        return user


class User(AbstractUser, BaseModel, PermissionsMixin):
    """Users in the system"""
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True,
        blank=True,
        null=True
    )
    phone_number = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        blank=True,
        null=True
    )
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=255, choices=GenderChoices.choices, default=GenderChoices.OTHER)
    kind = models.CharField(max_length=255, choices=UserKind.choices, default=UserKind.UNDEFINED)
    image = VersatileImageField(
        "profile_image",
        upload_to=get_user_media_file_prefix,
        blank=True,
        null=True
    )
    auth_provider = models.CharField(
        max_length=50,
        choices=AuthProvider.choices,
        default=AuthProvider.EMAIL
    )

    objects = UserManager()
    USERNAME_FIELD = "email"  # Or switch to phone_number as needed
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email or self.phone_number

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class UserProfile(BaseModel):
    """Profile for additional stuff information (e.g., staff introduction, scores)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    introduction = models.TextField(blank=True, null=True)  # Only applicable for staff
    total_score = models.PositiveIntegerField(default=0)  # Only applicable for staff

    def __str__(self):
        return f"Profile of {self.user.name}"


class Like(BaseModel):
    """Tracks which staff members a consumer likes."""
    consumer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="liked_staff", limit_choices_to={"kind": UserKind.CONSUMER}
    )
    staff = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="likes", limit_choices_to={"kind": UserKind.RESTAURANT_STUFF}
    )

    class Meta:
        unique_together = ("consumer", "staff")  # Prevent duplicate likes

    def __str__(self):
        return f"{self.consumer.name} likes {self.staff.name}"


post_save.connect(post_save_user, sender=User)
