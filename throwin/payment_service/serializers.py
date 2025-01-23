import logging

from django.conf import settings
from rest_framework import serializers

from accounts.choices import UserKind
from accounts.models import User

from store.models import Restaurant, Store

from .models import PaymentHistory

domain = settings.SITE_DOMAIN

logger = logging.getLogger(__name__)


class MakePaymentSerializer(serializers.ModelSerializer):
    staff_uid = serializers.UUIDField(write_only=True)  # Reference staff by UID
    restaurant_uid = serializers.UUIDField(write_only=True)  # Reference restaurant by UID
    store_uid = serializers.UUIDField(write_only=True, required=False)  # Reference store by UID (optional)

    class Meta:
        model = PaymentHistory
        fields = ["staff_uid", "restaurant_uid", "store_uid", "nickname", "amount", "currency", "payment_method", "message"]

    def validate_staff_uid(self, value):
        """
        Validate that the staff UID corresponds to a valid restaurant staff user.
        """
        try:
            staff = User.objects.get(uid=value, kind=UserKind.RESTAURANT_STAFF)
            return staff
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid staff UID: Staff does not exist or is not a restaurant staff.")

    def validate_restaurant_uid(self, value):
        """
        Validate that the restaurant UID corresponds to a valid restaurant.
        """
        try:
            restaurant = Restaurant.objects.get(uid=value)
            return restaurant
        except Restaurant.DoesNotExist:
            raise serializers.ValidationError("Invalid restaurant UID: Restaurant does not exist.")

    def validate_store_uid(self, value):
        """
        Validate that the store UID corresponds to a valid store (if provided).
        """
        if value:
            try:
                store = Store.objects.get(uid=value)
                return store
            except Store.DoesNotExist:
                raise serializers.ValidationError("Invalid store UID: Store does not exist.")
        return None

    def validate(self, data):
        """
        Cross-validate staff, restaurant, and store relationships.
        """
        staff = data["staff_uid"]
        restaurant = data["restaurant_uid"]
        store = data.get("store_uid")

        logger.info(f"Validating staff: {staff}, restaurant: {restaurant}, store UID: {store}")

        # Check if the staff belongs to the specified restaurant
        if not restaurant.restaurant_users.filter(user=staff).exists():
            logger.error(f"Validation failed: Staff {staff.email} does not belong to the restaurant {restaurant.name}.")
            raise serializers.ValidationError("The selected staff does not belong to the specified restaurant.")

        # Check if the store belongs to the specified restaurant (if provided)
        if store and store.restaurant != restaurant:
            logger.error(f"Validation failed: Store {store.name} does not belong to the restaurant {restaurant.name}.")
            raise serializers.ValidationError("The selected store does not belong to the specified restaurant.")

        # Replace UIDs with actual objects in the validated data
        data["staff"] = staff
        data["restaurant"] = restaurant
        data["store"] = store
        return data

    def create(self, validated_data):
        """
        Create a payment history record with the given validated data.
        """
        # Extract validated instances
        staff = validated_data.pop("staff")
        restaurant = validated_data.pop("restaurant")
        store = validated_data.pop("store", None)  # Optional

        # Remove raw UID fields from validated_data
        validated_data.pop("staff_uid", None)
        validated_data.pop("restaurant_uid", None)
        validated_data.pop("store_uid", None)

        # Handle authenticated customer details
        request_user = self.context["request"].user
        if request_user.is_authenticated:
            validated_data["customer"] = request_user
            validated_data["nickname"] = request_user.username
        else:
            validated_data["nickname"] = validated_data.get("nickname", "Anonymous")

        # Create the payment record
        payment = PaymentHistory.objects.create(
            staff=staff,
            restaurant=restaurant,
            store=store,
            **validated_data,  # This will include fields like `amount`, `currency`, etc.
        )

        logger.info(f"Payment created successfully: {payment}")
        return payment




class PaymentHistorySerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.name", read_only=True)
    customer_name = serializers.CharField(source="customer.username", read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)
    service_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    net_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = PaymentHistory
        fields = [
            "transaction_id",
            "nickname",
            "staff_name",
            "restaurant_name",
            "store_name",
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
    """
    Serializer for staff users to see their own payment histories.
    """
    customer_name = serializers.CharField(source="customer.username", read_only=True)
    nickname = serializers.CharField(read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = PaymentHistory
        fields = [
            "transaction_id",
            "customer_name",
            "nickname",
            "restaurant_name",
            "store_name",
            "amount",
            "currency",
            "status",
            "payment_date",
            "payment_method",
        ]


class ConsumerPaymentHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for consumers to see their own payment histories.
    """
    staff_name = serializers.CharField(source="staff.name", read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)
    staff_image = serializers.SerializerMethodField()

    class Meta:
        model = PaymentHistory
        fields = [
            "transaction_id",
            "staff_name",
            "restaurant_name",
            "store_name",
            "amount",
            "currency",
            "status",
            "payment_date",
            "payment_method",
            "staff_image",
        ]

    def get_staff_image(self, obj):
        """
        Get the staff user's profile image.
        """
        if obj.staff.image:
            try:
                return {
                    "small": domain + obj.staff.image.crop["400x400"].url,
                    "medium": domain + obj.staff.image.crop["600x600"].url,
                    "large": domain + obj.staff.image.crop["1000x1000"].url,
                    "full_size": domain + obj.staff.image.url,
                }
            except Exception as e:
                return {"error": str(e)}
        return None

class RestaurantOwnerPaymentHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for restaurant owners to see payment histories for their restaurants.
    """
    staff_name = serializers.CharField(source="staff.name", read_only=True)
    customer_name = serializers.CharField(source="customer.username", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = PaymentHistory
        fields = [
            "transaction_id",
            "customer_name",
            "nickname",
            "staff_name",
            "store_name",
            "amount",
            "currency",
            "status",
            "payment_date",
            "payment_method",
        ]


class AdminPaymentHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for admins to see all payment histories.
    """
    staff_name = serializers.CharField(source="staff.name", read_only=True)
    customer_name = serializers.CharField(source="customer.username", read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)
    service_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    net_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = PaymentHistory
        fields = [
            "transaction_id",
            "customer_name",
            "nickname",
            "staff_name",
            "restaurant_name",
            "store_name",
            "amount",
            "currency",
            "status",
            "payment_date",
            "payment_method",
            "service_fee",
            "net_amount",
            "is_distributed",
        ]



class StaffRecentMessagesSerializer(serializers.ModelSerializer):
    """
    Serializer to send the last 5 messages for a staff's transactions.
    """
    date = serializers.DateTimeField(source="payment_date", read_only=True)  # Map to 'payment_date' explicitly
    message = serializers.CharField(read_only=True)  # Keep this as it is
    nickname = serializers.CharField(read_only=True)  # No 'source' required because field name matches the model

    class Meta:
        model = PaymentHistory
        fields = ["message", "date", "nickname"]