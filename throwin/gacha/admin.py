from django.contrib import admin

from gacha.models import SpinBalance, GachaHistory


class SpinBalanceAdmin(admin.ModelAdmin):
    """Admin configuration for SpinBalance model."""
    list_display = ["uid","id", "consumer", "store", "restaurant", "total_spend", "used_spend", "remaining_spend", "total_spin", "used_spin", "remaining_spin"]
    search_fields = ["consumer__name", "consumer__email", "store__name", "store__code", "store__uid", "restaurant__name", "restaurant__uid"]
    list_filter = ["store", "restaurant", "consumer"]

    def get_queryset(self, request):
        """Optimize queries for SpinBalance admin."""
        return super().get_queryset(request).select_related("consumer", "store", "restaurant")


admin.site.register(SpinBalance, SpinBalanceAdmin)


class GachaHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for GachaHistory model."""
    list_display = ["uid", "id", "consumer", "store", "gacha_kind", "is_consumed", "consumed_at", "created_at"]
    search_fields = ["consumer__name", "consumer__email", "store__name", "store__code", "store__uid", "store__name", "gacha_kind"]
    list_filter = ["store", "gacha_kind", "is_consumed", "created_at"]

    def get_queryset(self, request):
        """Optimize queries for GachaHistory admin."""
        return super().get_queryset(request).select_related("consumer", "store")


admin.site.register(GachaHistory, GachaHistoryAdmin)