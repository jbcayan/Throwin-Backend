from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
    PermissionsMixin
)
from django.db import models

from versatileimagefield.fields import VersatileImageField

from accounts.choices import GenderChoices, UserKind

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
    gender = models.CharField(max_length=255, choices=GenderChoices.choices, default=GenderChoices.OTHER)
    kind = models.CharField(max_length=255, choices=UserKind.choices, default=UserKind.UNDEFINED)
    image = VersatileImageField(
        "profile_image",
        upload_to=get_user_media_file_prefix,
        blank=True,
        null=True
    )

    objects = UserManager()
    USERNAME_FIELD = "email"  # Or switch to phone_number as needed
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email or self.phone_number

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
