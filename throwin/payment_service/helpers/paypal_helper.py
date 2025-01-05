import paypalrestsdk
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging for PayPal integration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": os.getenv("PAYPAL_MODE", "sandbox"),  # sandbox or live
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
})


def create_paypal_payment(amount, currency, description, return_url, cancel_url):
    """
    Create a PayPal payment and return the response object.
    """
    try:
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "transactions": [{
                "amount": {
                    "total": f"{amount:.2f}",
                    "currency": currency
                },
                "description": description
            }],
            "redirect_urls": {
                "return_url": return_url,
                "cancel_url": cancel_url
            }
        })

        if payment.create():
            logger.info(f"PayPal Payment created successfully: {payment.id}")
            return {"success": True, "payment": payment}
        else:
            logger.error(f"PayPal Payment creation failed: {payment.error}")
            return {"success": False, "error": payment.error}
    except Exception as e:
        logger.exception("An error occurred while creating PayPal payment.")
        return {"success": False, "error": str(e)}


def execute_paypal_payment(payment_id, payer_id):
    """
    Execute an approved PayPal payment.
    """
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        if payment.execute({"payer_id": payer_id}):
            logger.info(f"PayPal Payment executed successfully: {payment.id}")
            return {"success": True, "payment": payment}
        else:
            logger.error(f"PayPal Payment execution failed: {payment.error}")
            return {"success": False, "error": payment.error}
    except Exception as e:
        logger.exception("An error occurred while executing PayPal payment.")
        return {"success": False, "error": str(e)}
