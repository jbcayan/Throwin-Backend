from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connections
from django.db.utils import OperationalError

class HealthCheckView(APIView):
    def get(self, request):
        # Check if the database is accessible
        db_status = "ok"
        try:
            connections["default"].cursor()
        except OperationalError:
            db_status = "fail"

        # Return a response with status and a message
        return Response({
            "status": "ok",
            "message": "Application is running smoothly",
            "database": db_status
        }, status=status.HTTP_200_OK)
