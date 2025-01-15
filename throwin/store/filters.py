from django_filters import rest_framework as filters
from store.models import Store, StoreUser, Restaurant, RestaurantUser


class StoreFilter(filters.FilterSet):
    """Filter for store."""

    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    code = filters.CharFilter(field_name="code", lookup_expr="icontains")

    class Meta:
        model = Store
        fields = ["name", "code", "restaurant"]
