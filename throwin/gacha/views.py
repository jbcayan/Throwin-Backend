from rest_framework import generics, status
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from common.permissions import (
    IsConsumerUser,
)

from gacha.models import SpinBalance, GachaHistory
from gacha.serializers import (
    AvailableSpinsSerializer,
    PlayGachaSerializer,
    GachaTicketListSerializer,
)


# Create your views here.
@extend_schema(
    summary="1. Check available spins per store for the authenticated user.",
)
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
        ).values("store__uid", "store__name", "remaining_spin")
        except AttributeError as e:
            return SpinBalance.objects.none()

@extend_schema(
    summary="2. Play gacha for the authenticated user and get the result (Bronze, Silver, Gold).",
)
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

@extend_schema(
    summary="3. Get a list of available gacha results for the authenticated user.",
)
class GachaTicketList(generics.ListAPIView):
    """
    API to get available spins per store for the authenticated user.
    """
    permission_classes = [IsConsumerUser]
    serializer_class = GachaTicketListSerializer
    pagination_class = None


    def get_queryset(self):
        try:
            return GachaHistory.objects.filter(
            consumer=self.request.user,
            is_consumed=False
        ).select_related(
            "store",
            )
        except AttributeError as e:
            return SpinBalance.objects.none()