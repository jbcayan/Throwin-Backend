from django.db import models

class GMOCreditPayment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CAPTURE", "Captured"),
        ("FAILED", "Failed"),
        ("CANCELED", "Canceled"),
    ]

    order_id = models.CharField(max_length=50, unique=True, db_index=True)
    customer = models.CharField(max_length=255)  # Customer identifier
    store = models.CharField(max_length=255)  # Store identifier
    staff = models.CharField(max_length=255)  # Staff identifier
    restaurant = models.CharField(max_length=255)  # Restaurant identifier
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    access_id = models.CharField(max_length=100, blank=True, null=True)
    access_pass = models.CharField(max_length=100, blank=True, null=True)
    
    token = models.CharField(max_length=512, blank=True, null=True)  # Store token for token-based payments
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    approval_code = models.CharField(max_length=50, blank=True, null=True)
    process_date = models.DateTimeField(blank=True, null=True)
    
    card_last4 = models.CharField(max_length=4, blank=True, null=True)  # Masked card details
    expire_date = models.CharField(max_length=5, blank=True, null=True)  # Card expiry (MMYY)
    
    forward = models.CharField(max_length=100, blank=True, null=True)  # Payment forwarding info
    pay_method = models.CharField(max_length=50, blank=True, null=True)  # Payment method type
    
    is_distributed = models.BooleanField(default=False)  # Distribution status
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.status}"
