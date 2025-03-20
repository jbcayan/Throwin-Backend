import os
import json
import calendar
import time
from datetime import date
import requests
from celery import shared_task
from django.conf import settings
from django.db import transaction
from dotenv import load_dotenv

# Load environment variables from your .env file.
load_dotenv()

# Retrieve PayPal base URL and client credentials from environment variables.
BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
CLIENT_ID = os.getenv("Paypal_Disbursement_AC_CLIENT_ID")
CLIENT_SECRET = os.getenv("Paypal_Disbursement_AC_CLIENT_SECRET")

from payment_service.gmo_pg.models import Balance
from payment_service.gmo_pg.models import PayPalDetail, PayPalDisbursement


def get_access_token():
    """Get OAuth 2.0 access token from PayPal."""
    url = f"{BASE_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US"
    }
    data = {
        "grant_type": "client_credentials"
    }
    
    response = requests.post(
        url, 
        auth=(CLIENT_ID, CLIENT_SECRET), 
        headers=headers,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Access token obtained successfully. Expires in {result.get('expires_in')} seconds")
        return result['access_token']
    else:
        print(f"Error getting access token: {response.text}")
        return None


def create_batch_payout(recipients):
    """
    Send money to multiple recipients via PayPal.
    
    recipients: List of dictionaries with recipient details.
    """
    access_token = get_access_token()
    if not access_token:
        return None
    
    url = f"{BASE_URL}/v1/payments/payouts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    # Create a unique batch ID.
    batch_id = f"batch_{int(time.time())}"
    
    items = []
    for i, recipient in enumerate(recipients):
        item = {
            "recipient_type": recipient.get("type", "EMAIL"),
            "amount": {
                "value": str(recipient["amount"]),
                "currency": recipient.get("currency", "JPY")
            },
            "receiver": recipient["receiver"],
            "note": recipient.get("note", "Payment from Python app"),
            "sender_item_id": recipient["sender_item_id"]
        }
        items.append(item)
    
    payload = {
        "sender_batch_header": {
            "sender_batch_id": batch_id,
            "email_subject": "Throwin Received!",
            "email_message": "You have received a payment from Throwin."
        },
        "items": items
    }
    
    print(f"Sending batch payment to {len(items)} recipients...")
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"Batch payout created successfully with batch ID: {batch_id}")
        return result
    else:
        print(f"Error creating batch payout: {response.status_code}")
        print(f"Response: {response.text}")
        return None


@shared_task
# @shared_task(name='payment_service.gmo_pg.tasks.disburse_paypal_payments')
def disburse_paypal_payments():
    """
    Scheduled task (via Celery Beat) to run on the last day of every month.
    It checks all users with a balance of at least 3000 JPY and initiates a PayPal batch payout.
    """

    
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    
    # Proceed only if today is the last day of the month.
    if today.day != last_day:
        return "Today is not the last day of the month. Task exited."
    
    # Retrieve all balances where current_balance is >= 3000 JPY.
    eligible_balances = Balance.objects.filter(current_balance__gte=3000)
    
    recipients = []
    disbursement_records = {}
    
    for balance in eligible_balances:
        user = balance.user
        
        # Retrieve PayPal details: try individual first, then shared based on user's role.
        paypal_detail = None
        try:
            paypal_detail = PayPalDetail.objects.get(user=user)
        except PayPalDetail.DoesNotExist:
            if user.kind == "fc_admin":
                paypal_detail = PayPalDetail.objects.filter(account_type="fc_admin").first()
            elif user.kind == "glow_admin":
                paypal_detail = PayPalDetail.objects.filter(account_type="glow_admin").first()
        
        if not paypal_detail:
            # Skip users without PayPal details.
            continue
        
        amount = balance.current_balance
        
        # Create a disbursement record in PENDING state.
        record = PayPalDisbursement.objects.create(
            user=user,
            amount=amount,
            status="PENDING"
        )
        
        recipient = {
            "receiver": paypal_detail.paypal_email,
            "amount": amount,
            "currency": "JPY",
            "note": "Payout for your available balance.",
            "sender_item_id": str(user.id)
        }
        recipients.append(recipient)
        disbursement_records[str(user.id)] = (record, balance)
    
    # If no recipients, exit the task.
    if not recipients:
        return "No eligible recipients for payout."
    
    # Create a batch payout for all eligible recipients.
    result = create_batch_payout(recipients)
    
    if result:
        payout_batch_id = result.get("batch_header", {}).get("payout_batch_id")
        # Update all disbursement records as COMPLETED and deduct the amount.
        for user_id, (record, balance) in disbursement_records.items():
            record.transaction_id = payout_batch_id
            record.status = "COMPLETED"
            record.save()
            with transaction.atomic():
                balance.current_balance -= record.amount
                balance.save()
        return f"Batch payout completed with batch ID: {payout_batch_id}"
    else:
        # Mark all records as FAILED if batch payout creation fails.
        for user_id, (record, _) in disbursement_records.items():
            record.status = "FAILED"
            record.message = "Batch payout creation failed."
            record.save()
        return "Batch payout failed."
