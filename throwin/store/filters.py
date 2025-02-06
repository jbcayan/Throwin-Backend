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


class StaffFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="user__name", lookup_expr='icontains')
    email = filters.CharFilter(field_name="user__email", lookup_expr='icontains')
    phone_number = filters.CharFilter(field_name="user__phone_number", lookup_expr='icontains')
    public_status = filters.CharFilter(field_name="user__public_status", lookup_expr='iexact')

    class Meta:
        model = RestaurantUser
        fields = ['name', 'email', 'phone_number']


class StaffUserFilter(filters.FilterSet):
    store_uid = filters.CharFilter(field_name="store__uid")
    store_code = filters.CharFilter(field_name="store__code")

    class Meta:
        model = StoreUser
        fields = ["store_uid", "store_code"]
