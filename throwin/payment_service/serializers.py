from rest_framework import serializers
from .models import PaymentHistory, DisbursementRequest, DisbursementStatus  
from accounts.models import User
from accounts.choices import UserKind
from django.db.models import Sum


class PaymentHistorySerializer(serializers.ModelSerializer):
    staff = serializers.UUIDField()

    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'customer', 'staff', 'customer_uuid', 'staff_uuid', 'amount',
            'transaction_id', 'status', 'payment_method', 'anonymous',
            'customer_email', 'customer_username', 'customer_phone', 'user_nick_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['transaction_id', 'status', 'created_at', 'updated_at']

    def validate_staff(self, value):
        """
        Ensure the staff exists and is a valid restaurant staff user.
        """
        if not User.objects.filter(uid=value, kind=UserKind.RESTAURANT_STAFF).exists():
            raise serializers.ValidationError("Invalid staff UUID or user is not a restaurant staff member.")
        return value

    def validate(self, data):
        """
        Cross-field validation for anonymous payments.
        """
        if data.get("anonymous") and data.get("customer"):
            raise serializers.ValidationError("Anonymous payments cannot have an associated customer.")
        return data


class DisbursementRequestSerializer(serializers.ModelSerializer):
    staff_uuid = serializers.UUIDField(source='staff.id', read_only=True)
    processed_by_uuid = serializers.UUIDField(source='processed_by.id', read_only=True)

    class Meta:
        model = DisbursementRequest
        fields = ['id', 'staff', 'amount', 'status', 'processed_by', 'created_at', 'updated_at']
        read_only_fields = ['staff', 'processed_by', 'created_at', 'updated_at']

    def validate_amount(self, value):
        """
        Validate that the disbursement amount is positive and within the available balance.
        """
        staff = self.context['request'].user
        balance = self.get_balance(staff)
        if value <= 0:
            raise serializers.ValidationError("Disbursement amount must be positive.")
        if value > balance:
            raise serializers.ValidationError("Insufficient balance for this disbursement request.")
        return value

    def validate_status(self, value):
        """
        Validate the status transition rules.
        """
        request_user = self.context['request'].user
        current_status = self.instance.status if self.instance else None

        # Only admins can mark requests as in-progress or rejected
        if value in [DisbursementStatus.IN_PROGRESS, DisbursementStatus.REJECTED] and not request_user.is_superuser:
            raise serializers.ValidationError("Only admins can mark requests as in-progress or rejected.")

        # Only in-progress requests can be marked as completed or failed
        if value == DisbursementStatus.COMPLETED and current_status != DisbursementStatus.IN_PROGRESS:
            raise serializers.ValidationError("Only in-progress requests can be marked as completed.")
        if value == DisbursementStatus.REJECTED and current_status != DisbursementStatus.IN_PROGRESS:
            raise serializers.ValidationError("Only in-progress requests can be marked as rejected.")

        return value

    def get_balance(self, staff):
        """
        Calculate the available balance for a staff member.
        """
        total_received = staff.received_payments.completed().aggregate(
            total=Sum('amount')
        )['total'] or 0

        total_requested = staff.disbursement_requests.filter(
            status__in=[DisbursementStatus.PENDING, DisbursementStatus.IN_PROGRESS]
        ).aggregate(total=Sum('amount'))['total'] or 0

        return total_received - total_requested

    def create(self, validated_data):
        """
        Automatically set the status to 'pending' during creation.
        """
        validated_data['status'] = DisbursementStatus.PENDING
        return super().create(validated_data)
