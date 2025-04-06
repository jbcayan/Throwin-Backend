import logging

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema

from rest_framework import generics, status
from rest_framework.response import Response

from accounts.choices import UserKind
from common.permissions import (
    IsFCAdminUser,
    IsGlowAdminUser,
    IsSalesAgentUser,
    CheckAnyPermission,
    IsRestaurantOwnerUser,
    IsSuperAdminUser
)

from store.models import Restaurant
from store.rest.serializers.fc_glow_sales_agents import (
    OrganizationCreateSerializer,
    OrganizationListSerializer,
    ActivationNewUserSerializer,
    SalesAgentListCreateSerializer,
    ActivationSerializer,
    AdminsChangeEmailRequestSerializer, ChangeAdminNameSerializer,
)
from django.db import transaction


logger = logging.getLogger(__name__)
User = get_user_model()


@extend_schema(
    summary="List and Create organization by FC, GLOW, Sales Agent",
    methods=["GET", "POST"],
)
class OrganizationListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and create restaurant organizations.
    Uses the OrganizationCreateSerializer for both representation and creation.
    """
    available_permission_classes = (
        IsFCAdminUser,
        IsGlowAdminUser,
        IsSalesAgentUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the request method.
        """
        if self.request.method == "POST":
            return OrganizationCreateSerializer
        return OrganizationListSerializer

    def get_queryset(self):
        """
        Return all active restaurant organizations.
        """
        return Restaurant.objects.all().select_related('restaurant_owner')

    def create(self, request, *args, **kwargs):
        """
        Handles POST requests to create a new organization.
        Returns key details of the created restaurant upon success.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            restaurant = serializer.save()
        except Exception as e:
            logger.error("Error during organization creation: %s", str(e))
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use the serializer's to_representation to format the response data.
        response_data = serializer.to_representation(restaurant)
        return Response(response_data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Retrieve, update or delete organization by FC, GLOW, Sales Agent",
    methods=["GET", "PUT", "PATCH", "DELETE"],
)
class OrganizationRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update, or delete a restaurant organization.
    The restaurant instance is looked up by its uid provided in the URL kwargs.
    Uses the OrganizationCreateSerializer for both representation and updating.
    """

    available_permission_classes = (
        IsFCAdminUser,
        IsGlowAdminUser,
        IsSalesAgentUser,
    )
    permission_classes = (CheckAnyPermission,)  # Update with appropriate permission classes

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the request method.
        """
        if self.request.method in ["PUT", "PATCH"]:
            return OrganizationCreateSerializer
        return OrganizationListSerializer

    def get_object(self):
        """
        Retrieve the Restaurant instance by its uid provided in the URL kwargs.
        """
        uid = self.kwargs.get('uid')
        return get_object_or_404(Restaurant, uid=uid)

    def update(self, request, *args, **kwargs):
        """
        Update the restaurant organization and return the updated representation.
        """
        partial = kwargs.pop('partial', False)  # Ensure partial updates are allowed
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        # Return the customized representation using the serializer's to_representation method.
        return Response(
            serializer.to_representation(updated_instance),
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        """
        Delete the restaurant organization.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ActivateNewAccountView(generics.GenericAPIView):
    """
    API endpoint to activate a user's account.
    """
    serializer_class = ActivationNewUserSerializer

    @extend_schema(
        request=ActivationNewUserSerializer,
        responses={200: 'Account activated successfully.'}
    )
    @transaction.atomic
    def post(self, request, uidb64, token, *args, **kwargs):
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        serializer = self.serializer_class(data=
        {
            'uidb64': uidb64,
            'token': token,
            'password': password,
            'confirm_password': confirm_password
        })
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.set_password(password)
            user.is_verified = True
            user.is_active = True
            user.save(
                update_fields=[
                    'password',
                    'is_verified',
                    'is_active',
                ]
            )
            return Response({
                "detail": "Account activated successfully."
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Activate a user's account and change email for FC, Glow, Sales Agent and Restaurant Owner",
)
class ActivateAccountView(generics.GenericAPIView):
    """
    API endpoint to activate a user's account.
    """
    def get(self, request, uidb64, token, *args, **kwargs):
        serializer = ActivationSerializer(data={'uidb64': uidb64, 'token': token})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_email = serializer.validated_data.get('new_email')
            if new_email:
                user.email = new_email
                user.is_verified = True
                user.save(update_fields=['email', 'is_verified'])
            return Response({
                "detail": "Account activated successfully."
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="List and Create Sales Agents",
    methods=["GET", "POST"],
)
class SalesAgentListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and create sales agents.
    Uses the SalesAgentCreateSerializer for both representation and creation.
    """
    serializer_class = SalesAgentListCreateSerializer
    available_permission_classes = (
        IsFCAdminUser,
        IsGlowAdminUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_queryset(self):
        """
        Return the queryset of sales agents.
        """
        return User.objects.filter(kind=UserKind.SALES_AGENT)

    def create(self, request, *args, **kwargs):
        """
        Handles POST requests to create a new sales agent.
        Returns key details of the created agent upon success.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            sales_agent = serializer.save()
        except Exception as e:
            logger.error("Error during sales agent creation: %s", str(e))
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        response_data = serializer.to_representation(sales_agent)
        return Response(response_data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Retrieve, update or delete Sales Agent",
    methods=["GET", "PUT", "PATCH", "DELETE"],
)
class SalesAgentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update, or delete a sales agent.
    The sales agent instance is looked up by its uid provided in the URL kwargs.
    Uses the SalesAgentDetailSerializer for both representation and updating.
    """
    serializer_class = SalesAgentListCreateSerializer
    available_permission_classes = (
        IsFCAdminUser,
        IsGlowAdminUser,
        IsSalesAgentUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_queryset(self):
        """
        Return the queryset of sales agents.
        """
        return User.objects.filter(kind=UserKind.SALES_AGENT)

    def get_object(self):
        """
        Retrieve the User instance by its uid provided in the URL kwargs.
        """
        queryset = self.get_queryset()
        uid = self.kwargs.get('uid')
        return get_object_or_404(queryset, uid=uid)

    def update(self, request, *args, **kwargs):
        """
        Update the sales agent and return the updated representation.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        return Response(
            serializer.to_representation(updated_instance),
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        """
        Delete the sales agent.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

@extend_schema(
    summary="Request email change for FC, GLOW, Sales Agent and Restaurant Owner",
    methods=["POST"],
)
class AdminsChangeEmailRequestView(generics.GenericAPIView):
    """
    API endpoint for restaurant owners to request an email change.
    """
    available_permission_classes = (
        IsRestaurantOwnerUser,
        IsFCAdminUser,
        IsGlowAdminUser,
        IsSuperAdminUser,
        IsSalesAgentUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = AdminsChangeEmailRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "detail": "Activation link sent to the new email."
        }, status=status.HTTP_200_OK)

@extend_schema(
    summary="Change the FC, GLOW, Sales Agent name.",
    methods=["POST"],
)
class AdminChangeNameView(generics.CreateAPIView):
    available_permission_classes = (
        IsSuperAdminUser,
        IsGlowAdminUser,
        IsFCAdminUser,
        IsSalesAgentUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ChangeAdminNameSerializer