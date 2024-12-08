"""Filter for user"""
from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    NumberFilter,
)

from django.contrib.auth import get_user_model

User = get_user_model()


class UserFilter(FilterSet):
    """Filter for user"""

    name = CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = User
        fields = ["name"]
