"""Uls for FC, Glow and Sales Agent"""
from django.urls import path

from store.rest.views.fc_glow_sales_agents import (
    OrganizationListCreateView,
    OrganizationRetrieveUpdateDestroy,
    ActivateNewAccountView,
    SalesAgentListCreateView,
    SalesAgentRetrieveUpdateDestroyView,
    ActivateAccountView,
    AdminsChangeEmailRequestView,
    AdminChangeNameView,
    FcGlowAgentAccountDetailsView,
)

urlpatterns = [
    path("/organizations", OrganizationListCreateView.as_view(),
        name="organization-create"
    ),
    path("/organizations/<str:uid>", OrganizationRetrieveUpdateDestroy.as_view(),
        name="organization-detail"
    ),
    path('/activate/new/account/<uidb64>/<token>', ActivateNewAccountView.as_view(),
         name='activate-new-account'
    ),
    path('/activate/<uidb64>/<token>', ActivateAccountView.as_view(),
        name='activate-account'
    ),
    path("/settings/change-email-request", AdminsChangeEmailRequestView.as_view(),
         name="change-email-request"
         ),
    path("/sales-agents", SalesAgentListCreateView.as_view(),
        name="sales-agent-list-create"
    ),
    path("/sales-agents/<str:uid>", SalesAgentRetrieveUpdateDestroyView.as_view(),
        name="sales-agent-detail"
    ),
    path("/settings/change-name", AdminChangeNameView.as_view(),
         name="change-name"
    ),
    path("/settings", FcGlowAgentAccountDetailsView.as_view(),
         name="fc-glow-settings"
         ),
]