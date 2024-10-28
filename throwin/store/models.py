import random

from django.db import models
from django.db.models import UniqueConstraint

from versatileimagefield.fields import VersatileImageField

from common.models import BaseModel

from core.utils import get_store_banner_file_prefix, get_store_logo_file_prefix

from store.choices import StoreUserRole
from store.utils import generate_store_code


# Create your models here.
class Store(BaseModel):
    """Model to represent a store/restaurant."""
    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
    )  # Unique store code
    description = models.TextField(blank=True, null=True)
    logo = VersatileImageField(
        "Store logo",
        upload_to=get_store_logo_file_prefix,
        blank=True,
        null=True
    )
    banner = VersatileImageField(
        "Banner image",
        upload_to=get_store_banner_file_prefix,
        blank=True,
        null=True
    )  # Optional banner image

    def save(self, *args, **kwargs):
        """Generate a unique store code if not provided."""
        if not self.code:
            while True:
                self.code = generate_store_code(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Store'
        verbose_name_plural = 'Stores'
        ordering = ['-created_at']


class StoreUser(BaseModel):
    """Model to represent a store user. (This model is for admin and staff only) """
    store = models.ForeignKey(
        "store.Store",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE
    )
    role = models.CharField(
        max_length=50,
        choices=StoreUserRole.choices,
        default=StoreUserRole.UNDEFINED
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ('store', 'user')
        constraints = [
            UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="User can only have one default store",
                violation_error_message="A user can only have one default store"
            )
        ]

    def __str__(self):
        return f"{self.user} is a {self.role} of {self.store}"
