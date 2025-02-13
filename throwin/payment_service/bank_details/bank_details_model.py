from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from common.models import BaseModel
from accounts.models import User

class BankAccount(BaseModel):
    """Stores multiple bank accounts for each user, with one active at a time"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('futsuu', '普通 - Savings'),
        ('toza', '当座 - Current'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bank_accounts"
    )
    bank_name = models.CharField(
        max_length=100,
        help_text="Name of the bank (e.g., Mitsubishi UFJ, Mizuho, SMBC)"
    )
    bank_code = models.CharField(
        max_length=4,
        validators=[
            RegexValidator(r'^\d{4}$', 'Bank code must be exactly 4 digits.')
        ],
        help_text="4-digit bank code"
    )
    branch_name = models.CharField(
        max_length=100,
        help_text="Branch name of the bank"
    )
    branch_code = models.CharField(
        max_length=3,
        validators=[
            RegexValidator(r'^\d{3}$', 'Branch code must be exactly 3 digits.')
        ],
        help_text="3-digit branch code"
    )
    account_number = models.CharField(
        max_length=16,  # Some corporate accounts can have more than 7 digits
        validators=[
            MinLengthValidator(7),
            RegexValidator(r'^\d{7,16}$', 'Account number must be between 7-16 digits.')
        ],
        help_text="Bank account number (7-16 digits)"
    )
    account_type = models.CharField(
        max_length=10,
        choices=ACCOUNT_TYPE_CHOICES,
        default='futsuu',
        help_text="Type of account: Savings (普通) or Current (当座)"
    )
    account_holder_name = models.CharField(
        max_length=100,
        help_text="Account holder name in Katakana"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Only one account can be active at a time."
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'account_number')

    def save(self, *args, **kwargs):
        """Ensure only one bank account is active per user"""
        if self.is_active:
            BankAccount.objects.filter(user=self.user).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number} ({'Active' if self.is_active else 'Inactive'})"
