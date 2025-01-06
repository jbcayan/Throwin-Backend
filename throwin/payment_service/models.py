from decimal import Decimal
from django.db import models
from common.models import BaseModel
from accounts.models import User
from accounts.choices import UserKind


class PaymentHistory(BaseModel):
    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        limit_choices_to={"kind": UserKind.CONSUMER},
        help_text="Authenticated customer making the payment (nullable for anonymous)"
    )
    nickname = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Nickname for the customer (anonymous or user-provided)"
    )
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_payments",
        limit_choices_to={"kind": UserKind.RESTAURANT_STAFF},
        help_text="The staff receiving the payment"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount in the selected currency"
    )
    currency = models.CharField(
        max_length=10,
        default="JPY",
        help_text="Currency of the payment"
    )
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique identifier for the transaction from PayPal"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
            ("canceled", "Canceled"),
        ],
        default="pending",
        help_text="Payment transaction status"
    )
    is_distributed = models.BooleanField(
        default=False,
        help_text="Indicates whether the payment has been distributed to the staff"
    )
    payment_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time of the payment initiation"
    )
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ("paypal", "PayPal"),
            ("stripe", "Stripe"),
            ("cash", "Cash"),
        ],
        default="paypal",
        help_text="Payment method used by the customer"
    )
    service_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.0"),
        help_text="Transaction fee deducted by the payment gateway"
    )
    net_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Net amount received after deducting service fees"
    )

    def save(self, *args, **kwargs):
        """
        Override the save method to calculate service fee and net amount.
        """
        service_fee_rate = Decimal("0.036")  # 3.6%
        fixed_fee = Decimal("40")  # 40 JPY

        if not self.service_fee:  # Calculate service fee only if not set
            self.service_fee = (self.amount * service_fee_rate) + fixed_fee

        if not self.net_amount:  # Calculate net amount only if not set
            self.net_amount = self.amount - self.service_fee

        super().save(*args, **kwargs)

    def clean(self):
        """
        Validate that the payment amount is positive.
        """
        from django.core.exceptions import ValidationError
        if self.amount <= 0:
            raise ValidationError("Payment amount must be greater than zero.")
        super().clean()

    def __str__(self):
        return f"{self.transaction_id or 'Pending'} - {self.amount} {self.currency}"

    class Meta:
        ordering = ["-payment_date"]
        verbose_name = "Payment History"
        verbose_name_plural = "Payment Histories"
