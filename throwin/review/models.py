import uuid
from django.db import models
from common.models import BaseModel


class Review(BaseModel):
    """
    Represents a review left by a customer for a specific payment/tip.
    """
    payment = models.ForeignKey(
        'payment_service.GMOCreditPayment',
        on_delete=models.SET_NULL, # Keep review even if payment is deleted
        blank=True,
        null=True,
        related_name="reviews",
        help_text="The payment transaction this review is associated with."
    )
    payment_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="The type of payment this review is associated with."
    )
    transaction_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="The transaction ID of the payment this review is associated with."
    )
    consumer = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reviews_consumer",
        help_text="The consumer who wrote the review."
    )
    consumer_name = models.CharField(
        max_length=50,
        default="Anonymous",
        help_text="The name of the consumer who wrote the review.",

    )
    message = models.TextField(
        help_text="The content of the customer's review message."
    )
    store_uid = models.UUIDField(
        default=uuid.uuid4, blank=True, null=True, db_index=True,
        help_text="Unique identifier for store (optional)"
    )
    staff_uid = models.UUIDField(
        default=uuid.uuid4, blank=True, null=True, db_index=True,
        help_text="Unique identifier for staff receiving the tip"
    )

    def __str__(self):
        return f"{self.consumer_name} - {self.message[:10]}..."

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Review"
        verbose_name_plural = "Reviews"


class Reply(BaseModel):
    """
    Represents a reply to a Review or another Reply,
    allowing for threaded conversations.
    """
    review = models.ForeignKey(
        'review.Review',
        on_delete=models.CASCADE, # If the original review is deleted, delete replies
        related_name="replies",
        help_text="The initial review this reply belongs to."
    )
    parent_reply = models.ForeignKey(
        'self', # Self-referential key for threading
        on_delete=models.CASCADE, # If a parent reply is deleted, delete its children
        null=True,
        blank=True,
        related_name="child_replies",
        help_text="The direct parent reply, if this is a reply to another reply."
    )
    restaurant_owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL, # Keep reply even if author account is deleted
        blank=True,
        null=True, # Allows for deleted users
        related_name="replies_restaurant_owner",
        help_text="The user (restaurant owner) who wrote the reply."
    )
    consumer = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL, # Keep reply even if author account is deleted
        blank=True,
        null=True, # Allows for deleted users
        related_name="replies_consumed",
        help_text="The user (consumer) who wrote the reply."
    )
    message = models.TextField(
        help_text="The content of the reply message."
    )

    def __str__(self):
        if self.consumer:
            return f"{self.consumer} - {self.message[:10]}..."
        else:
            return f"{self.restaurant_owner} - {self.message[:10]}..."

    class Meta:
        ordering = ["created_at"] # Order replies chronologically within a thread
        verbose_name = "Reply"
        verbose_name_plural = "Replies"