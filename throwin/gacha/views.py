from rest_framework import generics, status

from rest_framework.response import Response

from common.permissions import (
    IsConsumerUser,
)
from gacha.models import SpinBalance

from gacha.serializers import (
    AvailableSpinsSerializer,
    PlayGachaSerializer,
)


# Create your views here.
class AvailableSpinsView(generics.ListAPIView):
    """
    API to get available spins per store for the authenticated user.
    """
    permission_classes = [IsConsumerUser]
    serializer_class = AvailableSpinsSerializer

    def get_queryset(self):
        try:
            return SpinBalance.objects.filter(
            consumer=self.request.user,
            remaining_spin__gt=0
        ).values("store__id", "remaining_spin")
        except AttributeError as e:
            return SpinBalance.objects.none()


class PlayGacha(generics.GenericAPIView):
    """
    API to play gacha for the authenticated user.
    """
    permission_classes = [IsConsumerUser]
    serializer_class = PlayGachaSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Validate and raise errors if any
        result = serializer.save()  # Play the gacha and update the spin balance

        return Response(
            {"result": result},
            status=status.HTTP_200_OK
        )