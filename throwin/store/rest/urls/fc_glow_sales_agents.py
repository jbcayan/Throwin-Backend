"""Uls for FC, Glow and Sales Agent"""
from django.urls import path

from store.rest.views.fc_glow_sales_agents import (
    OrganizationListCreateView,
    OrganizationRetrieveUpdateDestroy,
    ActivateAccountView
)

urlpatterns = [
    path("/organizations", OrganizationListCreateView.as_view(),
        name="organization-create"
    ),
    path("/organizations/<str:uid>", OrganizationRetrieveUpdateDestroy.as_view(),
        name="organization-detail"
    ),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(),
        name='activate-account'
    ),
]