"""Urls for gacha related views."""

from django.urls import path

from gacha.views import (
    AvailableSpinsView,
    PlayGacha,
    GachaTicketList,
)

urlpatterns = [
    path("/available-spins", AvailableSpinsView.as_view()),
    path("/play", PlayGacha.as_view()),
    path("/tickets", GachaTicketList.as_view()),
]