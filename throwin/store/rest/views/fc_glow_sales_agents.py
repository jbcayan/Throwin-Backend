import logging
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, OpenApiParameter

from rest_framework import generics, status
from rest_framework.response import Response

from common.permissions import (
    IsFCAdminUser,
    IsGlowAdminUser,
    IsSalesAgentUser,
    CheckAnyPermission
)

from store.rest.serializers.fc_glow_sales_agents import (
    OrganizationCreateSerializer,
    OrganizationListSerializer,
)
from store.models import Restaurant, Store, StoreUser, RestaurantUser

logger = logging.getLogger(__name__)


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
