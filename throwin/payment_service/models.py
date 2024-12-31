from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import F
from decimal import Decimal
import uuid
from accounts.models import User
from accounts.choices import UserKind
from common.models import BaseModel


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class DisbursementStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    REJECTED = 'rejected', 'Rejected'


class PaymentHistoryManager(models.Manager):
    def completed(self):
        """Filter payments that are marked as completed."""
        return self.filter(status=PaymentStatus.COMPLETED)


class PaymentHistory(BaseModel):
    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'kind': UserKind.CONSUMER},
        related_name="payments"
    )
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'kind': UserKind.RESTAURANT_STAFF},
        related_name="received_payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(
        max_length=50,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    anonymous = models.BooleanField(default=False)
    customer_email = models.EmailField(blank=True, null=True)
    customer_username = models.CharField(max_length=50, blank=True, null=True)
    customer_phone = models.CharField(max_length=15, blank=True, null=True)
    user_nick_name = models.CharField(max_length=50, blank=True, null=True)

    objects = PaymentHistoryManager()

    def save(self, *args, **kwargs):
        """Override save method to populate customer details for non-anonymous payments."""
        if self.customer and not self.anonymous:
            self.customer_email = self.customer.email
            self.customer_username = self.customer.username
            self.customer_phone = self.customer.phone_number
            self.user_nick_name = self.customer.username
        elif self.anonymous and not self.user_nick_name:
            self.user_nick_name = "Anonymous User"
        super().save(*args, **kwargs)

    def __str__(self):
        customer_info = self.customer or self.user_nick_name or "Anonymous"
        return f"Payment of {self.amount} to {self.staff.name} by {customer_info}"

    class Meta:
        ordering = ['-created_at']


class Balance(BaseModel):
    staff = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'kind': UserKind.RESTAURANT_STAFF},
        related_name="balance"
    )
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_disbursed = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    management_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    glow_share = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    sales_agency_share = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    franchise_share = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def update_balance(self, payment):
        """
        Update balances based on the payment received.
        Handles PayPal fees, staff shares, and management share splits.
        """
        paypal_fee_percentage = Decimal("0.036")
        fixed_paypal_fee = Decimal("40.00")
        staff_share_percentage = Decimal("0.75")
        management_share_percentage = Decimal("0.25")
        glow_share_percentage = Decimal("0.30")
        sales_agency_share_percentage = Decimal("0.40")
        franchise_share_percentage = Decimal("0.30")

        try:
            # Calculate balances
            paypal_fee = (payment.amount * paypal_fee_percentage) + fixed_paypal_fee
            remaining_balance = payment.amount - paypal_fee
            staff_share = remaining_balance * staff_share_percentage
            management_share = remaining_balance * management_share_percentage

            # Management splits
            glow_share = management_share * glow_share_percentage
            sales_agency_share = management_share * sales_agency_share_percentage
            franchise_share = management_share * franchise_share_percentage

            # Use F expressions for atomic updates
            self.total_earned = F('total_earned') + staff_share
            self.management_balance = F('management_balance') + management_share
            self.glow_share = F('glow_share') + glow_share
            self.sales_agency_share = F('sales_agency_share') + sales_agency_share
            self.franchise_share = F('franchise_share') + franchise_share
            self.save()
            self.refresh_from_db()  # Refresh the object to retrieve the updated values

        except Exception as e:
            raise ValidationError(f"Error updating balance: {str(e)}")

    def get_available_balance(self):
        """Return the available balance for disbursements."""
        return self.total_earned - self.total_disbursed

    def __str__(self):
        return f"Balance for {self.staff.name}"


class DisbursementRequest(BaseModel):
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'kind': UserKind.RESTAURANT_STAFF},
        related_name="disbursement_requests"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=DisbursementStatus.choices,
        default=DisbursementStatus.PENDING
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_disbursements"
    )

    def clean(self):
        """Ensure the disbursement amount is valid and within available balance."""
        if self.amount <= 0:
            raise ValidationError("Disbursement amount must be positive.")
        try:
            available_balance = self.staff.balance.get_available_balance()
            if self.amount > available_balance:
                raise ValidationError("Insufficient balance for this disbursement request.")
        except AttributeError:
            raise ValidationError("Staff balance record is missing. Please contact support.")

    def __str__(self):
        return f"Disbursement of {self.amount} by {self.staff.name}"

    class Meta:
        ordering = ['-created_at']
