from rest_framework import serializers
from django.conf import settings
from .models import GMOCreditPayment
import uuid
import requests
import logging

logger = logging.getLogger(__name__)

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GMO PG Credentials
GMO_API_URL = os.getenv("GMO_API_URL")
GMO_SHOP_ID = os.getenv("GMO_SHOP_ID")
GMO_SHOP_PASS = os.getenv("GMO_SHOP_PASS")


from datetime import datetime

# Convert GMO's date format (YYYYMMDDHHMMSS) to Django's format (YYYY-MM-DD HH:MM:SS)
def convert_gmo_date(gmo_date):
    if gmo_date and len(gmo_date) == 14:  # Ensure correct length
        return datetime.strptime(gmo_date, "%Y%m%d%H%M%S")
    return None

class GMOCreditPaymentSerializer(serializers.ModelSerializer):
    staff_uid = serializers.UUIDField(write_only=True)  # Reference staff by UID
    restaurant_uid = serializers.UUIDField(write_only=True)  # Reference restaurant by UID
    store_uid = serializers.UUIDField(write_only=True, required=False)  # Optional store UID
    sales_agent_uid = serializers.UUIDField(write_only=True, required=False)  # Optional sales agent UID
    token = serializers.CharField(write_only=True, required=True)  # Token is required for payment execution

    class Meta:
        model = GMOCreditPayment
        fields = [
            "order_id", "nickname", "staff_uid", "restaurant_uid", "store_uid", "sales_agent_uid",
            "amount", "currency", "token", "status", "transaction_id", "approval_code", "process_date",
            "card_last4", "expire_date", "pay_method", "forward", "created_at"
        ]
        read_only_fields = [
            "order_id", "status", "transaction_id", "approval_code", "process_date",
            "card_last4", "expire_date", "pay_method", "forward", "created_at"
        ]

    def validate_amount(self, value):
        """Ensure amount is numeric and greater than zero."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, data):
        """
        Cross-validate staff, restaurant, and store relationships.
        """
        staff_uid = data["staff_uid"]
        restaurant_uid = data["restaurant_uid"]
        store_uid = data.get("store_uid")

        # Validation logic for staff belonging to the restaurant
        # (Assuming we have a function to verify this)
        if not self._is_staff_of_restaurant(staff_uid, restaurant_uid):
            raise serializers.ValidationError("The selected staff does not belong to the specified restaurant.")

        # Validation logic for store belonging to the restaurant
        if store_uid and not self._is_store_of_restaurant(store_uid, restaurant_uid):
            raise serializers.ValidationError("The selected store does not belong to the specified restaurant.")

        return data

    def _is_staff_of_restaurant(self, staff_uid, restaurant_uid):
        """Check if the staff belongs to the restaurant (Placeholder function)."""
        # Implement logic to verify staff's restaurant relationship
        return True

    def _is_store_of_restaurant(self, store_uid, restaurant_uid):
        """Check if the store belongs to the restaurant (Placeholder function)."""
        # Implement logic to verify store's restaurant relationship
        return True

    def create(self, validated_data):
        """
        Step 1: Register Payment (`EntryTran`)
        Step 2: Execute Payment using Token (`ExecTran`)
        """
        staff_uid = validated_data["staff_uid"]
        restaurant_uid = validated_data["restaurant_uid"]
        store_uid = validated_data.get("store_uid")
        sales_agent_uid = validated_data.get("sales_agent_uid")
        amount = validated_data["amount"]
        token = validated_data["token"]
        customer = self.context["request"].user if self.context["request"].user.is_authenticated else None
        nickname = customer.username if customer else validated_data.get("nickname", "Anonymous")

        # Generate a unique Order ID
        order_id = f"ORDER{uuid.uuid4().hex[:12]}"

        # Step 1: Register the Payment (`EntryTran`)
        entry_payload = {
            "ShopID": GMO_SHOP_ID,
            "ShopPass": GMO_SHOP_PASS,
            "OrderID": order_id,
            "JobCd": "CAPTURE",
            "Amount": int(amount),
            "TdFlag": "1",
        }

        entry_response = self._send_gmo_request(f"{GMO_API_URL}/payment/EntryTran.idPass", entry_payload)

        # Extract access details from the response
        access_id = entry_response.get("AccessID")
        access_pass = entry_response.get("AccessPass")

        if not access_id or not access_pass:
            logger.error("Invalid EntryTran response: %s", entry_response)
            raise serializers.ValidationError({"error": "Invalid EntryTran response", "details": entry_response})

        # Step 2: Execute Payment using Token (`ExecTran`)
        exec_payload = {
            "AccessID": access_id,
            "AccessPass": access_pass,
            "OrderID": order_id,
            "Method": "1",
            "Token": token,
        }

        exec_response = self._send_gmo_request(f"{GMO_API_URL}/payment/ExecTran.idPass", exec_payload)

        # Create and store payment record in DB
        payment = GMOCreditPayment.objects.create(
            order_id=order_id,
            customer=customer,
            nickname=nickname,
            staff_uid=staff_uid,
            restaurant_uid=restaurant_uid,
            store_uid=store_uid,
            sales_agent_uid=sales_agent_uid,
            amount=amount,
            currency="JPY",
            access_id=access_id,
            access_pass=access_pass,
            token=token,
            status=exec_response.get("ACS", "PENDING"),
            transaction_id=exec_response.get("TranID"),
            approval_code=exec_response.get("Approve"),
            process_date=convert_gmo_date(exec_response.get("TranDate")),
            card_last4="****" + exec_response.get("CardNo", "")[-4:],
            expire_date=exec_response.get("Expire"),
            forward=exec_response.get("Forward"),
            pay_method=exec_response.get("Method"),
        )

        logger.info("Payment successfully created: %s", payment.order_id)
        return payment

    def _send_gmo_request(self, url, payload):
        """Send a request to the GMO API and handle response."""
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
            return dict(item.split("=") for item in response.text.split("&"))
        except requests.exceptions.RequestException as e:
            logger.error("GMO API request failed: %s", str(e))
            raise serializers.ValidationError({"error": "Failed to communicate with GMO API", "details": str(e)})
        except Exception as e:
            logger.error("Unexpected error during GMO API communication: %s", str(e))
            raise serializers.ValidationError({"error": "Unexpected error during GMO API communication", "details": str(e)})
