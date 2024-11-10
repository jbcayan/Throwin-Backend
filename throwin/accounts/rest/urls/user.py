"""Urls for user"""

from django.urls import path

from accounts.rest.views.user import (
    SetUserName,
    AccountActivation,
    EmailChangeRequest,
    VerifyEmailChange,
    StuffDetailForConsumer,
    ConsumerLikeStuffCreateDestroy,
    FavoriteStuffList,
    Me,
)

urlpatterns = [
    path(
        "/me",
        Me.as_view(),
        name="me"
    ),
    path(
        "/name",
        SetUserName.as_view(),
        name="user-name"
    ),
    path(
        "/acivate/<str:uidb64>/<str:token>",
        AccountActivation.as_view(),
        name="activate-account"
    ),
    path(
        "/email-change-reqquest",
        EmailChangeRequest.as_view(),
        name="email-change-request"
    ),
    path(
        "/email-verify",
        VerifyEmailChange.as_view(),
        name="verify-email-change"
    ),
    path(
        "/stuff/<uuid:uid>",
        StuffDetailForConsumer.as_view(),
        name="stuff-detail-for-consumer"
    ),
    path(
        "/stuff/<uuid:uid>/like",
        ConsumerLikeStuffCreateDestroy.as_view(),
        name="consumer-like-stuff"
    ),
    path(
        "/favorite-stuff",
        FavoriteStuffList.as_view(),
        name="favorite-stuff"
    ),

]
