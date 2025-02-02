from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.choices import Status

from gacha.models import SpinBalance, GachaHistory
from gacha.utils import Gacha

from store.choices import GachaTicketEnabled
from store.models import Store

User = get_user_model()

class AvailableSpinsSerializer(serializers.Serializer):
    store_id = serializers.IntegerField(source="store__id")
    available_spin = serializers.IntegerField(source="remaining_spin")


class PlayGachaSerializer(serializers.Serializer):
    store_uid = serializers.UUIDField()

    def validate_store_uid(self, value):
        """
        Validate that the store_uid corresponds to an active store with gacha enabled.
        """
        try:
            store = Store.objects.get(
                uid=value,
                status=Status.ACTIVE,
                gacha_enabled=GachaTicketEnabled.YES
            )
        except Store.DoesNotExist as e:
            raise ValidationError("Invalid store_uid.") from e
        return store

    def validate(self, attrs):
        """
        Validate that the user has enough spins to play the gacha.
        """
        store = attrs["store_uid"]
        user = self.context["request"].user

        try:
            spin_balance = SpinBalance.objects.get(
                consumer=user,
                store_id=store.id,
                remaining_spin__gt=0
            )
        except SpinBalance.DoesNotExist as e:
            raise ValidationError("You do not have enough spins to play gacha.") from e

        attrs["spin_balance"] = spin_balance
        return attrs

    def save(self, **kwargs):
        """
        Play the gacha, create a GachaHistory record, and update the SpinBalance.
        """
        spin_balance = self.validated_data["spin_balance"]
        user = self.context["request"].user

        # Play the gacha
        gacha = Gacha()
        result = gacha.play()

        # Create a GachaHistory record
        GachaHistory.objects.create(
            consumer=user,
            store=spin_balance.store,
            gacha_kind=result
        )

        # Update the spin balance
        spin_balance.used_spin += 1
        spin_balance.save()

        return result