from django.core.exceptions import ValidationError
from django.db import models

from versatileimagefield.fields import VersatileImageField

from accounts.choices import UserKind

from common.models import BaseModel

from core.utils import (
    get_restaurant_logo_file_prefix,
    get_restaurant_banner_file_prefix,
    get_store_logo_file_prefix,
    get_store_banner_file_prefix
)

from store.utils import (
    generate_store_code,
    generate_unique_slug
)


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
    restaurant_owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="restaurants",
        help_text="The owner of the restaurant",
    )
    sales_agent = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="sales_agent_restaurants",
        help_text="The sales agent of the restaurant",
    )

    def save(self, *args, **kwargs):
        # Generate slug from the restaurant name if it's not already set
        if not self.slug:
            self.slug = generate_unique_slug(self.name)
        super(Restaurant, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


# Create your models here.
class Store(BaseModel):
    """Model to represent a store/restaurant."""
    restaurant = models.ForeignKey(
        "store.Restaurant",
        on_delete=models.CASCADE,
        related_name="stores",
        blank=True,
        null=True,
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
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

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


class RestaurantUser(BaseModel):
    """
    Model to represent a restaurant user.
    SUPER_ADMIN, FC_ADMIN, and GLOW_ADMIN have implicit access to all restaurants.
    SALES_AGENT can have access to multiple restaurants.
    RESTAURANT_STAFF and RESTAURANT_OWNER have access to a single restaurant per account.
    """
    restaurant = models.ForeignKey(
        "store.Restaurant",
        on_delete=models.CASCADE,
        related_name="restaurant_users",
        help_text="The restaurant this user is assigned to. Null for global roles (not applicable)."
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="user_restaurants",
        help_text="The user associated with the restaurant."
    )
    role = models.CharField(
        max_length=50,
        choices=UserKind.choices,
        default=UserKind.UNDEFINED,
        help_text="The role of the user for the associated restaurant."
    )

    class Meta:
        constraints = [
            # Ensure that RESTAURANT_STAFF and RESTAURANT_OWNER have unique user-restaurant pair
            models.UniqueConstraint(
                fields=["user", "restaurant"],
                name="unique_user_restaurant_role",
                condition=models.Q(role__in=["restaurant_staff", "restaurant_owner"])
            ),
        ]

    def clean(self):
        """
        Validation to ensure proper role-specific constraints.
        Called before saving the model when using ModelForms or full_clean().
        """
        if not self.restaurant and self.role in ["restaurant_staff", "restaurant_owner"]:
            raise ValidationError(f"{self.role} must be associated with a specific restaurant.")
        if self.role in ["super_admin", "fc_admin", "glow_admin"]:
            raise ValidationError(f"{self.role} not needed restaurant user association.")

    def save(self, *args, **kwargs):
        """
        Enforce constraints dynamically before saving.
        """
        self.clean()  # Call the validation logic
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.role} - {self.restaurant}"


class StoreUser(BaseModel):
    """Model to represent a store user. (This model is for admin and staff only) """
    store = models.ForeignKey(
        "store.Store",
        on_delete=models.CASCADE,
        related_name="store_users",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="user_stores",
    )
    role = models.CharField(
        max_length=50,
        choices=UserKind.choices,
        default=UserKind.UNDEFINED,
        help_text="The role of the user in the store."
    )

    class Meta:
        unique_together = ("store", "user")  # Ensure a user can have only one role per store

    def __str__(self):
        return f"{self.user} - {self.role} - {self.store}"
