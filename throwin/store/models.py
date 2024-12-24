from django.db import models
from django.db.models import UniqueConstraint
from django.utils.text import slugify

from versatileimagefield.fields import VersatileImageField

from common.models import BaseModel

from core.utils import (
    get_restaurant_logo_file_prefix,
    get_restaurant_banner_file_prefix,
    get_store_logo_file_prefix,
    get_store_banner_file_prefix
)

from store.choices import StoreUserRole
from store.utils import generate_store_code


class Restaurant(BaseModel):
    """Model to represent a restaurant"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo = VersatileImageField(
        "restaurant logo",
        upload_to=get_restaurant_logo_file_prefix,
        blank=True,
        null=True
    )
    banner = VersatileImageField(
        "restaurant banner",
        upload_to=get_restaurant_banner_file_prefix,
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        # Generate slug from the restaurant name if it's not already set
        if not self.slug:
            self.slug = self.generate_unique_slug(self.name)
        super(Restaurant, self).save(*args, **kwargs)

    def generate_unique_slug(self, name):
        # Generate a slug from the restaurant name and ensure it's unique
        slug = slugify(name)
        unique_slug = slug
        num = 1
        while Restaurant.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{slug}-{num}"
            num += 1
        return unique_slug

    def __str__(self):
        return self.name


# Create your models here.
class Store(BaseModel):
    """Model to represent a store/restaurant."""
    restaurant = models.ForeignKey(
        "store.Restaurant",
        on_delete=models.CASCADE,
        related_name="stores"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        blank=True,
        null=True,
    )  # Unique store code
    description = models.TextField(blank=True, null=True)
    logo = VersatileImageField(
        "Store logo",
        upload_to=get_store_logo_file_prefix,
        blank=True,
        null=True
    )
    banner = VersatileImageField(
        "Store Banner",
        upload_to=get_store_banner_file_prefix,
        blank=True,
        null=True
    )  # Optional banner image

    def save(self, *args, **kwargs):
        """Generate a unique store code if not provided."""
        if not self.code:
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
