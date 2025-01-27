from django_filters import rest_framework as filters
from store.models import Store, StoreUser, Restaurant, RestaurantUser


class StoreFilter(filters.FilterSet):
    """Filter for store."""

    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    code = filters.CharFilter(field_name="code", lookup_expr="icontains")
    location = filters.CharFilter(field_name="location", lookup_expr="icontains")
    exposure = filters.CharFilter(field_name="exposure", lookup_expr="iexact")

    class Meta:
        model = Store
        fields = [
            "name",
            "code",
            "restaurant",
            "location",
            "exposure",
        ]
