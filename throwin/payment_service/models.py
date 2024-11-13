from django.db import models
from accounts.models import User
from accounts.choices import UserKind
from common.models import BaseModel
from django.core.exceptions import ValidationError
import uuid

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
        limit_choices_to={'kind': UserKind.RESTAURANT_STUFF},
        related_name="received_payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=255, unique=True, blank=True)
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
        if not self.transaction_id:
            self.transaction_id = str(uuid.uuid4())
        if self.customer and not self.anonymous:
            self.customer_email = self.customer.email
            self.customer_username = self.customer.username
            self.customer_phone = self.customer.phone_number
            self.user_nick_name = self.customer.username
        elif not self.customer:
            self.user_nick_name = self.user_nick_name or "Anonymous User"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment of {self.amount} to {self.staff.name} by {self.customer or self.user_nick_name or 'Anonymous'}"

class DisbursementRequest(BaseModel):
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'kind': UserKind.RESTAURANT_STUFF},
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

    class Meta:
        verbose_name = "Disbursement Request"
        verbose_name_plural = "Disbursement Requests"

    def __str__(self):
        return f"Disbursement of {self.amount} by {self.staff.name}"

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Disbursement amount must be positive.")
        if not self.status:
            self.status = DisbursementStatus.PENDING