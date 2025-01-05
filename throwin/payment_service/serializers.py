from rest_framework import serializers
from .models import PaymentHistory
from accounts.models import User
from accounts.choices import UserKind


class MakePaymentSerializer(serializers.ModelSerializer):
    staff_uid = serializers.UUIDField(write_only=True)  # For referencing staff by UID

    class Meta:
        model = PaymentHistory
        fields = ["staff_uid", "nickname", "amount", "currency", "payment_method"]

    def validate_staff_uid(self, value):
        """
        Validate that the staff UID corresponds to a valid restaurant staff user.
        """
        try:
            staff = User.objects.get(uid=value, kind=UserKind.RESTAURANT_STAFF)
            return staff  # Return the staff instance for use in `create`
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid staff UID: Staff does not exist or is not a restaurant staff.")

    def validate_amount(self, value):
        """
        Ensure the payment amount is greater than zero.
        """
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        return value

    def validate(self, data):
        """
        Ensure nickname is provided for unauthenticated customers.
        """
        request_user = self.context["request"].user
        if not request_user.is_authenticated and not data.get("nickname"):
            raise serializers.ValidationError("Nickname is required for unauthenticated customers.")
        return data

    def create(self, validated_data):
        """
        Create a payment history record with the given validated data.
        """
        # Extract the staff instance from validated data
        staff = validated_data.pop("staff_uid")

        # Handle customer details
        request_user = self.context["request"].user
        if request_user.is_authenticated:
            validated_data["customer"] = request_user
            validated_data["nickname"] = request_user.username
        else:
            validated_data["nickname"] = validated_data.get("nickname", "Anonymous")

        # Create and return the payment history object
        return PaymentHistory.objects.create(
            staff=staff,
            **validated_data,
        )



class PaymentHistorySerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.name", read_only=True)
    customer_name = serializers.CharField(source="customer.username", read_only=True)
    service_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    net_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = PaymentHistory
        fields = [
            "transaction_id",
            "nickname",
            "staff_name",
            "customer_name",
            "amount",
            "currency",
            "status",
            "payment_date",
            "payment_method",
            "service_fee",
            "net_amount",
        ]


class StaffPaymentHistorySerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.username", read_only=True)
    nickname = serializers.CharField(read_only=True)

    class Meta:
        model = PaymentHistory
        fields = [
            "transaction_id",
            "customer_name",
            "nickname",
            "amount",
            "currency",
            "status",
            "payment_date",
            "payment_method",
        ]


class AdminPaymentHistorySerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.name", read_only=True)
    customer_name = serializers.CharField(source="customer.username", read_only=True)
    service_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    net_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = PaymentHistory
        fields = [
            "transaction_id",
            "customer_name",
            "nickname",
            "staff_name",
            "amount",
            "currency",
            "status",
            "payment_date",
            "payment_method",
            "service_fee",
            "net_amount",
            "is_distributed",
        ]
