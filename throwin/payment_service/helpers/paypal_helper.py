import paypalrestsdk
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging for PayPal integration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate environment variables
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")  # Default to sandbox mode
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
    logger.error("PayPal client credentials are missing. Please check your environment variables.")
    raise EnvironmentError("PayPal client credentials are not set in the environment variables.")

# Configure PayPal SDK
def configure_paypal():
    """
    Configure PayPal SDK and validate configuration.
    """
    try:
        paypalrestsdk.configure({
            "mode": PAYPAL_MODE,  # sandbox or live
            "client_id": PAYPAL_CLIENT_ID,
            "client_secret": PAYPAL_CLIENT_SECRET
        })
        logger.info(f"PayPal SDK configured successfully in {PAYPAL_MODE} mode.")
    except Exception as e:
        logger.error("Failed to configure PayPal SDK.")
        raise e

configure_paypal()


def create_paypal_payment(amount, currency, description, return_url, cancel_url):
    """
    Create a PayPal payment and return the response object.
    :param amount: Total payment amount (float or Decimal).
    :param currency: Currency code (e.g., 'USD', 'JPY').
    :param description: Description of the payment.
    :param return_url: URL to redirect to after successful payment approval.
    :param cancel_url: URL to redirect to if the payment is canceled.
    :return: Dictionary with the success status and payment/ error details.
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
            error_message = payment.error.get('message', 'Unknown error occurred.')
            logger.error(f"PayPal Payment creation failed: {error_message}")
            return {"success": False, "error": payment.error}
    except Exception as e:
        logger.exception("An error occurred while creating PayPal payment.")
        return {"success": False, "error": str(e)}


def execute_paypal_payment(payment_id, payer_id):
    """
    Execute an approved PayPal payment.
    :param payment_id: PayPal payment ID to be executed.
    :param payer_id: Payer ID provided by PayPal after payment approval.
    :return: Dictionary with the success status and payment/ error details.
    """
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        if payment.execute({"payer_id": payer_id}):
            logger.info(f"PayPal Payment executed successfully: {payment.id}")
            return {"success": True, "payment": payment}
        else:
            error_message = payment.error.get('message', 'Unknown error occurred.')
            logger.error(f"PayPal Payment execution failed: {error_message}")
            return {"success": False, "error": payment.error}
    except Exception as e:
        logger.exception("An error occurred while executing PayPal payment.")
        return {"success": False, "error": str(e)}
