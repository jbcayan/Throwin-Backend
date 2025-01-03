"""Urls for user"""

from django.urls import path

from accounts.rest.views.user import (
    SetUserName,
    AccountActivation,
    EmailChangeRequest,
    EmailChangeRequestVerify,
    StaffDetailForConsumer,
    FavoriteStaffList,
    Me,
    DeleteUser,
    StaffList,
    ConsumerLikeStaffToggle,
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
        "/email-change-request",
        EmailChangeRequest.as_view(),
        name="email-change-request"
    ),
    path(
        "/email-change-request/verify/<str:token>",
        EmailChangeRequestVerify.as_view(),
        name="verify-email-change"
    ),
    path(
        "/staff/<str:username>",
        StaffDetailForConsumer.as_view(),
        name="stuff-detail-for-consumer"
    ),
    path(
        "/staff/<uuid:uid>/like",
        ConsumerLikeStaffToggle.as_view(),
        name="consumer-like-stuff"
    ),
    path(
        "/favorite-staff",
        FavoriteStaffList.as_view(),
        name="favorite-stuff"
    ),
    path(
        "/delete",
        DeleteUser.as_view(),
        name="delete-user"
    ),
    path(
        "/staff-list",
        StaffList.as_view(),
        name="staff-list"
    ),
]
