from rest_framework import serializers
from .models import PaymentHistory, DisbursementRequest
from django.db import models

class PaymentHistorySerializer(serializers.ModelSerializer):
    customer_uuid = serializers.UUIDField(source='customer.id', read_only=True)
    staff_uuid = serializers.UUIDField(source='staff.id', read_only=True)
    customer_email = serializers.EmailField(read_only=True)
    customer_username = serializers.CharField(read_only=True)
    customer_phone = serializers.CharField(read_only=True)
    user_nick_name = serializers.CharField(required=False)

    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'customer', 'staff', 'customer_uuid', 'staff_uuid', 'amount',
            'transaction_id', 'status', 'payment_method', 'anonymous',
            'customer_email', 'customer_username', 'customer_phone', 'user_nick_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['transaction_id', 'status', 'created_at', 'updated_at']

    def validate(self, data):
        if data.get('customer') and data.get('anonymous'):
            raise serializers.ValidationError("Anonymous payments cannot include customer information.")
        return data

class DisbursementRequestSerializer(serializers.ModelSerializer):
    staff_uuid = serializers.UUIDField(source='staff.id', read_only=True)
    processed_by_uuid = serializers.UUIDField(source='processed_by.id', read_only=True)

    class Meta:
        model = DisbursementRequest
        fields = [
            'id', 'staff', 'staff_uuid', 'amount', 'status', 'processed_by',
            'processed_by_uuid', 'created_at', 'updated_at'
        ]
        read_only_fields = ['staff', 'processed_by', 'created_at', 'updated_at']

    def validate_amount(self, value):
        staff = self.context['request'].user
        current_balance = self.get_staff_balance(staff)

        if value <= 0:
            raise serializers.ValidationError("Disbursement amount must be positive.")
        
        if value > current_balance:
            raise serializers.ValidationError("Insufficient balance for this disbursement request.")
        
        return value

    def get_staff_balance(self, staff):
        """
        Calculates the current balance available for disbursement requests.
        This considers:
        - Completed payments received by the staff member.
        - Pending or in-progress disbursements which reduce available balance.
        """
        total_received = staff.received_payments.filter(status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        total_requested = staff.disbursement_requests.filter(
            status__in=['pending', 'in_progress']
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        return total_received - total_requested

    def validate_status(self, value):
        request_user = self.context['request'].user
        current_status = self.instance.status if self.instance else None

        # Only admins can change status to 'in_progress' or 'rejected'
        if value in ['in_progress', 'rejected'] and not request_user.is_superuser:
            raise serializers.ValidationError("Only admins can mark requests as in progress or rejected.")
        
        # Status transitions: Only 'in_progress' can move to 'completed' or 'failed'
        if value == 'completed' and current_status != 'in_progress':
            raise serializers.ValidationError("Only in-progress requests can be marked as completed.")
        if value == 'failed' and current_status != 'in_progress':
            raise serializers.ValidationError("Only in-progress requests can be marked as failed.")
        
        return value

    def create(self, validated_data):
        validated_data['status'] = 'pending'  # Set default status for new requests
        return super().create(validated_data)
