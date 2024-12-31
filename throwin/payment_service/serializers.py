from uuid import UUID
from rest_framework import serializers
from .models import PaymentHistory, DisbursementRequest, Balance, DisbursementStatus
from accounts.models import User
from accounts.choices import UserKind


class PaymentHistorySerializer(serializers.ModelSerializer):
    staff = serializers.UUIDField()
    payment_method = serializers.CharField(required=True)  # Ensure payment_method is mandatory

    # Predefined choices for payment methods
    SUPPORTED_PAYMENT_METHODS = ["credit_card", "paypal"]

    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'customer', 'staff', 'amount', 'transaction_id', 'status',
            'payment_method', 'anonymous', 'customer_email', 'customer_username',
            'customer_phone', 'user_nick_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['transaction_id', 'status', 'created_at', 'updated_at']

    def validate_staff(self, value):
        """
        Ensure the staff exists and is a valid restaurant staff user.
        """
        try:
            staff_uuid = UUID(str(value))  # Ensure it's a valid UUID
            staff_user = User.objects.get(uid=staff_uuid, kind=UserKind.RESTAURANT_STAFF)
        except (ValueError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid staff UUID or user is not a restaurant staff member.")
        return staff_user

    def validate_payment_method(self, value):
        """
        Ensure the payment method is supported and not null.
        """
        if not value:
            raise serializers.ValidationError("Payment method is required.")
        if value not in self.SUPPORTED_PAYMENT_METHODS:
            raise serializers.ValidationError(f"Unsupported payment method '{value}'. Supported methods: {', '.join(self.SUPPORTED_PAYMENT_METHODS)}.")
        return value

    def validate(self, data):
        """
        Cross-field validation for anonymous payments and amount.
        """
        request_user = self.context['request'].user
        if request_user.is_authenticated:
            # If user is authenticated, ensure `customer` is set and `anonymous` is False
            if data.get("anonymous", False):
                raise serializers.ValidationError("Logged-in users cannot mark payments as anonymous.")
            data["customer"] = request_user  # Automatically associate the logged-in user
        else:
            # For anonymous users, ensure `customer` is not set
            if data.get("customer"):
                raise serializers.ValidationError("Anonymous payments cannot have an associated customer.")

        # Ensure the amount is positive
        if data.get("amount", 0) <= 0:
            raise serializers.ValidationError("Payment amount must be positive.")

        return data


    def validate_user_nick_name(self, value):
        """
        Validate the nickname for anonymous payments.
        """
        if not value.isalnum():
            raise serializers.ValidationError("Nickname can only contain letters and numbers.")
        return value

    def create(self, validated_data):
        """
        Override create to handle balance updates.
        """
        staff_user = validated_data.pop("staff")  # Extract the validated staff User object
        try:
            # Create the payment instance
            payment = PaymentHistory.objects.create(**validated_data, staff=staff_user)

            # Update the staff's balance
            balance, _ = Balance.objects.get_or_create(staff=staff_user)
            balance.update_balance(payment)

            return payment
        except Exception as e:
            raise serializers.ValidationError(f"Failed to create payment or update balance: {str(e)}")



import logging
from rest_framework import serializers
from .models import DisbursementRequest, DisbursementStatus
from accounts.models import User
from accounts.choices import UserKind

logger = logging.getLogger(__name__)

class DisbursementRequestSerializer(serializers.ModelSerializer):
    processed_by = serializers.CharField(source='processed_by.username', read_only=True)

    class Meta:
        model = DisbursementRequest
        fields = ['id', 'staff', 'amount', 'status', 'processed_by', 'created_at', 'updated_at']
        read_only_fields = ['staff', 'processed_by', 'created_at', 'updated_at']

    def validate_amount(self, value):
        """
        Validate that the disbursement amount is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Disbursement amount must be positive.")
        return value

    def validate_status(self, value):
        """
        Validate the status transition rules.
        """
        request_user = self.context['request'].user
        current_status = self.instance.status if self.instance else None

        # Admin-only transitions
        if value in [DisbursementStatus.IN_PROGRESS, DisbursementStatus.REJECTED] and not request_user.is_superuser:
            raise serializers.ValidationError("Only admins can mark requests as in-progress or rejected.")

        # Allowed transitions for in-progress requests
        if value == DisbursementStatus.COMPLETED and current_status != DisbursementStatus.IN_PROGRESS:
            raise serializers.ValidationError("Only in-progress requests can be marked as completed.")
        if value == DisbursementStatus.REJECTED and current_status != DisbursementStatus.IN_PROGRESS:
            raise serializers.ValidationError("Only in-progress requests can be marked as rejected.")

        return value


    def create(self, validated_data):
        """
        Automatically set the staff field to the authenticated user during creation and validate balance.
        """
        staff = self.context['request'].user
        if not staff or staff.kind != UserKind.RESTAURANT_STAFF:
            raise serializers.ValidationError("Only restaurant staff can create disbursement requests.")

        amount = validated_data.get("amount")
        try:
            balance = staff.balance.get_available_balance()
            logger.debug(f"Checking available balance for staff {staff.id}: {balance}")
            if amount > balance:
                logger.warning(f"Disbursement amount {amount} exceeds available balance {balance}.")
                raise serializers.ValidationError("Insufficient balance for this disbursement request.")
        except AttributeError:
            logger.error(f"Balance record is missing for staff {staff.id}.")
            raise serializers.ValidationError("Staff balance record is missing. Please contact support.")

        validated_data['staff'] = staff
        validated_data['status'] = DisbursementStatus.PENDING

        try:
            return super().create(validated_data)
        except Exception as e:
            logger.error(f"Failed to create disbursement request for staff {staff.id}: {e}")
            raise serializers.ValidationError(f"Failed to create disbursement request: {str(e)}")

    def update(self, instance, validated_data):
        """
        Handle balance deduction when a disbursement is completed.
        """
        new_status = validated_data.get('status', instance.status)

        if new_status == DisbursementStatus.COMPLETED and instance.status != DisbursementStatus.COMPLETED:
            try:
                staff_balance = instance.staff.balance
                staff_balance.total_disbursed += instance.amount
                staff_balance.save()
                logger.debug(f"Balance updated for staff {instance.staff.id}. Total disbursed: {staff_balance.total_disbursed}")
            except AttributeError:
                logger.error(f"Balance record is missing for staff {instance.staff.id}.")
                raise serializers.ValidationError("Failed to update balance. Staff balance record might be missing.")

        return super().update(instance, validated_data)
