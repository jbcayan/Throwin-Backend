from django.http import JsonResponse
from django.utils import timezone
import uuid

def dummy_payment_view(request):
    # Simulate a realistic payment response
    response_data = {
        "transaction_id": str(uuid.uuid4()),  # Unique transaction identifier
        "status": "success",                  # Transaction status
        "amount": 50.00,                      # Simulated payment amount
        "currency": "USD",                    # Currency
        "timestamp": timezone.now().isoformat(),  # Current timestamp in ISO format
        "message": "Payment processed successfully",
    }
    return JsonResponse(response_data)
