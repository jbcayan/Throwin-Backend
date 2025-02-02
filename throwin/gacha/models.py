from django.db import models
from django.db.models import F

from common.models import BaseModel

from gacha.choices import GachaKind


# Create your models here.
class SpinBalance(BaseModel):
    """Model to represent a user's spin balance.
    We will use this model:
    1. when user make a payment to the store.
    2. When user play the gacha, we will use this model to check if user has enough spins.
    3. When user played the gacha, we will use this model to update the used spins and
        remaining spins will be updated automatically.
    """
    consumer = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="spin_balances",
        help_text="The consumer who has the spins"
    )
    store = models.ForeignKey(
        "store.Store",
        on_delete=models.CASCADE,
        related_name="spin_balances",
        help_text="The store where the spins are available"
    )
    restaurant = models.ForeignKey(
        "store.Restaurant",
        on_delete=models.CASCADE,
        related_name="spin_balances",
        help_text="The restaurant where the spins are available"
    )
    # (total_spend) This field will update when user make a payment
    # example = 0+2000->2000;
    # example = 2000+5000->7000
    total_spend = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total throwin amount per store"
    )
    used_spend = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total used throwin amount per store"
    )
    remaining_spend = models.GeneratedField(
        expression=F("total_spend") - F("used_spend"),
        output_field=models.DecimalField(max_digits=10, decimal_places=2),
        db_persist=True,
        help_text="Remaining throwin amount per store",
    )
    total_spin = models.PositiveIntegerField(
        help_text="Total spin per store",
        default=0,
    )
    used_spin = models.PositiveIntegerField(
        help_text="Total used spin per store",
        default=0,
    )
    remaining_spin = models.GeneratedField(
        expression=F("total_spin") - F("used_spin"),
        output_field=models.PositiveIntegerField(),
        db_persist=True,
        help_text="Remaining spin per store",
    )

    def save(self, *args, **kwargs):
        self.total_spin = int(self.total_spend // 3000)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.consumer.name} has {self.remaining_spin} spins at {self.store.name} ({self.restaurant.name})"

    class Meta:
        ordering = ["-created_at"]


class GachaHistory(BaseModel):
    store = models.ForeignKey(
        "store.Store",
        on_delete=models.CASCADE,
        related_name="gacha_store_histories",
        help_text="The store where the gacha is available"
    )
    consumer = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="gacha_histories",
        help_text="The consumer who played the gacha"
    )
    gacha_kind = models.CharField(
        max_length=10,
        choices=GachaKind.choices,
        help_text="Gacha kind (gold, silver, bronze)"
    )
    is_consumed = models.BooleanField(
        default=False,
        help_text="Whether the gacha was consumed"
    )
    consumed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="The date and time when the gacha was consumed"
    )


    def __str__(self):
        return f"{self.consumer.name} played {self.gacha_kind} gacha at {self.store.name}"

    class Meta:
        ordering = ["-created_at"]