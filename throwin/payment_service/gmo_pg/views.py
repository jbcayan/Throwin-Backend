from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import GMOCreditPayment
from .serializers import GMOCreditPaymentSerializer

class GMOCreditCardPaymentView(APIView):
    def post(self, request):
        """
        API to register and execute payment using GMO PG credit card.
        Endpoint: /gmo-pg/credit-card/
        """
        print(f"Received request data: {request.data}")
        serializer = GMOCreditPaymentSerializer(data=request.data)
        if serializer.is_valid():
            print("Serializer is valid. Saving payment...")
            payment = serializer.save()
            return Response(GMOCreditPaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
        print(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
