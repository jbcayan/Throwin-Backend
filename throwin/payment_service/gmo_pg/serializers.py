from rest_framework import serializers
from .models import GMOCreditPayment
import requests
import os
from decimal import Decimal
from datetime import datetime
import logging
import time

# Load environment variables
GMO_API_URL = os.getenv("GMO_API_URL")
GMO_SHOP_ID = os.getenv("GMO_SHOP_ID")
GMO_SHOP_PASS = os.getenv("GMO_SHOP_PASS")

# Set up logging
logger = logging.getLogger(__name__)

class GMOCreditPaymentSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(write_only=True)
    store = serializers.CharField(write_only=True)
    staff = serializers.CharField(write_only=True)
    restaurant = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True, required=True)  # Token is required to execute payment

    class Meta:
        model = GMOCreditPayment
        fields = [
            "order_id", "customer", "store", "staff", "restaurant", "amount", "token",
            "status", "transaction_id", "approval_code", "process_date",
            "card_last4", "expire_date", "pay_method", "forward", "is_distributed", "created_at"
        ]
        read_only_fields = [
            "order_id", "status", "transaction_id", "approval_code", "process_date",
            "card_last4", "expire_date", "pay_method", "forward", "is_distributed", "created_at"
        ]

    def validate_amount(self, value):
        """Ensure amount is numeric and properly formatted."""
        try:
            if isinstance(value, list):  # Handle the case where amount is passed as a list
                value = value[0]  # Extract the first element of the list

            value = Decimal(value)
            if value <= 0:
                raise serializers.ValidationError("Amount must be greater than zero.")
            return value
        except (ValueError, TypeError):
            raise serializers.ValidationError("Amount must be a valid number.")

    def create(self, validated_data):
        """
        Step 1: Register Payment
        Step 2: Execute Payment using token
        """
        store = validated_data["store"]
        staff = validated_data["staff"]
        restaurant = validated_data["restaurant"]
        customer = validated_data["customer"]
        amount = int(validated_data["amount"])
        token = validated_data["token"]

        # Generate a unique OrderID
        order_id = "ORDER" + datetime.now().strftime("%Y%m%d%H%M%S")

        # Step 1: Register the Payment
        entry_payload = {
            "ShopID": GMO_SHOP_ID,
            "ShopPass": GMO_SHOP_PASS,
            "OrderID": order_id,
            "JobCd": "CAPTURE",  # Immediate charge
            "Amount": str(amount),  # Ensure it's a string for GMO
            "TdFlag": "1",  # Enables 3D Secure
        }

        # Debugging: Log the entry payload
        logger.debug("Entry Payload: %s", entry_payload)

        # Step 1: Send request to GMO API (Payment Registration)
        entry_response = self._send_gmo_request(f"{GMO_API_URL}/payment/EntryTran.idPass", entry_payload)

        # Extract access details from the response
        access_id = entry_response.get("AccessID")
        access_pass = entry_response.get("AccessPass")

        if not access_id or not access_pass:
            logger.error("Invalid EntryTran response: %s", entry_response)
            raise serializers.ValidationError({"error": "Invalid EntryTran response", "details": entry_response})

        # Step 2: Execute Payment using token
        exec_payload = {
            "AccessID": access_id,
            "AccessPass": access_pass,
            "OrderID": order_id,
            "Method": "1",  # Single payment
            "Token": token,
        }

        # Debugging: Log the exec payload
        logger.debug("Exec Payload: %s", exec_payload)

        # Step 2: Send request to GMO API (Execute Payment)
        exec_response = self._send_gmo_request(f"{GMO_API_URL}/payment/ExecTran.idPass", exec_payload)

        # Create and store payment record in DB
        payment = GMOCreditPayment.objects.create(
            order_id=order_id,
            customer=customer,
            store=store,
            staff=staff,
            restaurant=restaurant,
            amount=amount,
            access_id=access_id,
            access_pass=access_pass,
            token=token,
            status=exec_response.get("ACS", "PENDING"),
            transaction_id=exec_response.get("TranID"),
            approval_code=exec_response.get("Approve"),
            process_date=datetime.strptime(exec_response.get("TranDate"), "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S"),
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

