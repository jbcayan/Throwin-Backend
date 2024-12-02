from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from payment_service.models import PaymentHistory, DisbursementRequest, PaymentStatus, DisbursementStatus
from accounts.choices import UserKind


class PaymentServiceTests(TestCase):
    def setUp(self):
        # Create test users
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="password123",
            kind=UserKind.CONSUMER
        )
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            kind=UserKind.RESTAURANT_STAFF
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            is_superuser=True
        )

        # Create an API client
        self.client = APIClient()

        # Base URLs
        self.payment_url = "/payment_service/payments/"
        self.staff_disbursement_url = "/payment_service/staff/disbursements/"
        self.admin_disbursement_url = "/payment_service/admin/disbursements/"

    def authenticate(self, user):
        """Authenticate a user and set the token in the client."""
        login_url = "/auth/"  # Update this to match your URL pattern
        login_data = {"email": user.email, "password": "password123"}
        response = self.client.post(login_url, login_data)
        
        # Ensure authentication succeeded
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            f"Authentication failed: Status {response.status_code}, Response {response.json()}"
        )
        
        # Extract and set the token
        tokens = response.json().get("data", {})
        access_token = tokens.get("access")
        if not access_token:
            raise AssertionError(f"Access token not found in the response: {response.content}")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")


    # Payment History Tests
    def test_logged_in_customer_payment(self):
        self.authenticate(self.customer)
        data = {
            "staff": str(self.staff.uid),
            "amount": 50.0,
            "anonymous": False
        }
        response = self.client.post(self.payment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], "50.00")
        self.assertEqual(response.data['staff'], self.staff.email)  # Updated assertion
        self.assertEqual(response.data['anonymous'], False)

    def test_anonymous_customer_payment_without_nickname(self):
        data = {
            "staff": str(self.staff.uid),
            "amount": 20.0,
            "anonymous": True
        }
        response = self.client.post(self.payment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], "20.00")
        self.assertEqual(response.data['anonymous'], True)
        self.assertEqual(response.data['user_nick_name'], "Anonymous User")

    def test_anonymous_customer_payment_with_nickname(self):
        data = {
            "staff": str(self.staff.uid),
            "amount": 30.0,
            "anonymous": True,
            "user_nick_name": "TipMaster"
        }
        response = self.client.post(self.payment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], "30.00")
        self.assertEqual(response.data['user_nick_name'], "TipMaster")

    def test_invalid_staff_uuid(self):
        data = {
            "staff": "invalid-uuid",
            "amount": 30.0,
            "anonymous": True
        }
        response = self.client.post(self.payment_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("staff", response.data)

    def test_logged_in_customer_payment_history(self):
        self.authenticate(self.customer)
        PaymentHistory.objects.create(
            customer=self.customer,
            staff=self.staff,
            amount=50.0,
            status=PaymentStatus.COMPLETED
        )
        response = self.client.get(self.payment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_staff_payment_history(self):
        self.authenticate(self.staff)
        PaymentHistory.objects.create(
            customer=self.customer,
            staff=self.staff,
            amount=50.0,
            status=PaymentStatus.COMPLETED
        )
        response = self.client.get(self.payment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    # Disbursement Request Tests
    def test_staff_create_disbursement_request(self):
        self.authenticate(self.staff)
        PaymentHistory.objects.create(
            customer=self.customer,
            staff=self.staff,
            amount=100.0,
            status=PaymentStatus.COMPLETED
        )
        data = {"amount": 50.0}
        response = self.client.post(self.staff_disbursement_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], "50.00")
        self.assertEqual(response.data['status'], "pending")

    def test_staff_disbursement_insufficient_balance(self):
        self.authenticate(self.staff)
        PaymentHistory.objects.create(
            customer=self.customer,
            staff=self.staff,
            amount=20.0,
            status=PaymentStatus.COMPLETED
        )
        data = {"amount": 50.0}
        response = self.client.post(self.staff_disbursement_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)

    def test_admin_view_all_payments(self):
        self.authenticate(self.admin)
        PaymentHistory.objects.create(
            customer=self.customer,
            staff=self.staff,
            amount=50.0,
            status=PaymentStatus.COMPLETED
        )
        response = self.client.get(self.payment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_admin_view_all_disbursements(self):
        self.authenticate(self.admin)
        DisbursementRequest.objects.create(
            staff=self.staff,
            amount=50.0,
            status=DisbursementStatus.PENDING
        )
        response = self.client.get(self.admin_disbursement_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_admin_update_disbursement_request(self):
        self.authenticate(self.admin)
        disbursement = DisbursementRequest.objects.create(
            staff=self.staff,
            amount=50.0,
            status=DisbursementStatus.PENDING
        )
        data = {"status": "in_progress"}
        url = f"{self.admin_disbursement_url}{disbursement.id}/"
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], "in_progress")
