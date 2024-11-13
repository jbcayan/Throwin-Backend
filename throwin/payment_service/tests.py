from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from payment_service.models import PaymentHistory, DisbursementRequest, PaymentStatus, DisbursementStatus
from accounts.choices import UserKind
from django.core.exceptions import ValidationError

User = get_user_model()

class PaymentHistoryTests(TestCase):

    def setUp(self):
        # Create consumer and staff users
        self.consumer = User.objects.create_user(
            email="consumer@example.com",
            password="password123",
            name="Consumer User",
            kind=UserKind.CONSUMER
        )
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            name="Staff User",
            kind=UserKind.RESTAURANT_STUFF
        )

    def test_payment_creation(self):
        payment = PaymentHistory.objects.create(
            customer=self.consumer,
            staff=self.staff,
            amount=Decimal('20.00'),
            status=PaymentStatus.PENDING,
            anonymous=False
        )
        self.assertIsNotNone(payment.id)
        self.assertEqual(payment.status, PaymentStatus.PENDING)
        self.assertEqual(payment.customer_email, self.consumer.email)
        self.assertTrue(payment.transaction_id is not None)

    def test_anonymous_payment(self):
        payment = PaymentHistory.objects.create(
            staff=self.staff,
            amount=Decimal('15.00'),
            status=PaymentStatus.PENDING,
            anonymous=True,
            user_nick_name="GuestUser"
        )
        self.assertEqual(payment.user_nick_name, "GuestUser")
        self.assertIsNone(payment.customer)

    def test_payment_str(self):
        payment = PaymentHistory.objects.create(
            customer=self.consumer,
            staff=self.staff,
            amount=Decimal('25.50')
        )
        self.assertEqual(
            str(payment),
            f"Payment of 25.50 to {self.staff.name} by {self.consumer}"
        )

    def test_completed_payment_manager(self):
        PaymentHistory.objects.create(
            customer=self.consumer,
            staff=self.staff,
            amount=Decimal('30.00'),
            status=PaymentStatus.COMPLETED
        )
        PaymentHistory.objects.create(
            customer=self.consumer,
            staff=self.staff,
            amount=Decimal('15.00'),
            status=PaymentStatus.PENDING
        )
        completed_payments = PaymentHistory.objects.completed()
        self.assertEqual(completed_payments.count(), 1)


class DisbursementRequestTests(TestCase):

    def setUp(self):
        # Create staff and admin users
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            name="Staff User",
            kind=UserKind.RESTAURANT_STUFF
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="adminpassword",
            name="Admin User",
            kind=UserKind.SUPER_ADMIN
        )

    def test_disbursement_request_creation(self):
        disbursement = DisbursementRequest.objects.create(
            staff=self.staff,
            amount=Decimal('100.00')
        )
        self.assertIsNotNone(disbursement.id)
        self.assertEqual(disbursement.status, DisbursementStatus.PENDING)

    def test_disbursement_negative_amount(self):
        disbursement = DisbursementRequest(
            staff=self.staff,
            amount=Decimal('-10.00')
        )
        with self.assertRaises(ValidationError):
            disbursement.full_clean()  # This should raise ValidationError due to negative amount

    def test_disbursement_str(self):
        disbursement = DisbursementRequest.objects.create(
            staff=self.staff,
            amount=Decimal('150.00')
        )
        self.assertEqual(
            str(disbursement),
            f"Disbursement of 150.00 by {self.staff.name}"
        )

    def test_disbursement_processed_by(self):
        disbursement = DisbursementRequest.objects.create(
            staff=self.staff,
            amount=Decimal('200.00'),
            processed_by=self.admin,
            status=DisbursementStatus.COMPLETED
        )
        self.assertEqual(disbursement.processed_by, self.admin)
        self.assertEqual(disbursement.status, DisbursementStatus.COMPLETED)

    def test_disbursement_status_default_pending(self):
        disbursement = DisbursementRequest.objects.create(
            staff=self.staff,
            amount=Decimal('75.00')
        )
        self.assertEqual(disbursement.status, DisbursementStatus.PENDING)
