import uuid
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
    PermissionsMixin
)
from django.db import models
from django.db.models.signals import post_save
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

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
        user.kind = UserKind.SUPER_ADMIN
        user.is_verified = True
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
        max_length=15,
        unique=True,
        db_index=True,
        blank=True,
        null=True
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True
    )
    username = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True
    )
    gender = models.CharField(
        max_length=20,
        choices=GenderChoices.choices,
        default=GenderChoices.OTHER)
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
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    kind = models.CharField(
        max_length=50,
        choices=UserKind.choices,
        default=UserKind.UNDEFINED
    )
    store = models.ForeignKey(
        "store.Store",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None
    )

    objects = UserManager()
    USERNAME_FIELD = "email"  # Or switch to phone_number as needed
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email or self.phone_number

    def save(self, *args, **kwargs):
        if self.username is None:
            byte_code = urlsafe_base64_encode(force_bytes(self.id))
            self.username = byte_code
        super().save(*args, **kwargs)

    @property
    def get_store(self):
        if self.kind == UserKind.RESTAURANT_STUFF:
            try:
                return self.storeuser_set.select_related("store").get(is_default=True).store
            except Exception:
                return None
        return None

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class UserProfile(BaseModel):
    """Profile for additional stuff information (e.g., staff introduction, scores)."""
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="profile"
    )
    introduction = models.TextField(
        blank=True,
        null=True
    )  # Only applicable for staff
    address = models.TextField(
        blank=True,
        null=True
    )  # applicable for consumers
    total_score = models.PositiveIntegerField(default=0)  # Only applicable for staff
    fun_fact = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Short fun fact about the user (e.g., 'Eating and laughing')"
    )  # Only applicable for staff

    def __str__(self):
        return f"Profile of {self.user.name}"


class Like(BaseModel):
    """Tracks which staff members a consumer likes."""
    consumer = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="liked_staff",
        limit_choices_to={"kind": UserKind.CONSUMER}
    )
    staff = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="likes",
        limit_choices_to={"kind": UserKind.RESTAURANT_STUFF}
    )

    class Meta:
        unique_together = ("consumer", "staff")  # Prevent duplicate likes

    def __str__(self):
        return f"{self.consumer.name} likes {self.staff.name}"


class TemporaryUser(BaseModel):
    """Temporary model to store unverified user data."""
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    token = models.CharField(max_length=255, unique=True)
    kind = models.CharField(
        max_length=50,
        choices=UserKind.choices,
        default=UserKind.UNDEFINED
    )

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        from accounts.utils import generate_token

        if not self.token:
            # Generate a unique token by uuid
            self.token = generate_token()
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']


post_save.connect(post_save_user, sender=User)
