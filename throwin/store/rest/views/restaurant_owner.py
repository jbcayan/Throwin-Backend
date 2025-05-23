"""Views for restaurant owner."""
from django.contrib.auth import get_user_model
from django.db.models import (
    Count,
    Q,
    F
)
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from accounts.choices import UserKind, PublicStatus
from common.permissions import (
    CheckAnyPermission,
    IsRestaurantOwnerUser
)
from gacha.choices import GachaKind
from payment_service.bank_details.bank_details_model import BankAccount
from review.models import Review
from store.filters import StoreFilter, StaffFilter
from store.models import Store, RestaurantUser, StoreUser, Restaurant
from store.rest.serializers.restaurant_owner import (
    StoreCreateSerializer,
    StoreListSerializer,
    StaffListSerializer,
    StaffCreateSerializer,
    StaffUserSerializer,
    GachaHistorySerializer,
    ChangeRestaurantOwnerNameSerializer,
    RestaurantOwnerDetailSerializer,
    RestaurantOwnerReplySerializer,
    RestaurantOwnerReviewListSerializer,
    RestaurantOwnerReviewRepliesSerializer
)

User = get_user_model()

@extend_schema(
    summary="List and Create Stores for Restaurant Owner",
    methods=["GET", "POST"],
)
class StoreListCreateView(generics.ListCreateAPIView):
    """View for restaurant owner to create or list stores."""

    filterset_class = StoreFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    available_permission_classes = (
        IsRestaurantOwnerUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StoreCreateSerializer
        return StoreListSerializer

    def get_queryset(self):
        # Get the restaurant of the logged in restaurant owner
        try:
            user_restaurant = self.request.user.get_restaurant_owner_restaurant

            return Store().get_all_actives().filter(
                restaurant_id=user_restaurant.id
            ).only(
                "uid",
                "name",
                "code",
                "restaurant",
                "exposure",
                "banner",
            ).select_related(
                "restaurant"
            )

        except AttributeError as e:
            return Store.objects.none()


@extend_schema(
    summary="Retrieve, Update, or Delete Store for Restaurant Owner",
    methods=["GET", "PUT", "PATCH", "DELETE"],
)
class StoreRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """View for restaurant owner to retrieve, update, or delete stores."""

    available_permission_classes = (
        IsRestaurantOwnerUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return StoreListSerializer
        return StoreCreateSerializer

    def get_object(self):
        try:
            user_restaurant = self.request.user.get_restaurant_owner_restaurant

            store = Store.objects.only(
                "uid",
                "name",
                "code",
                "restaurant",
                "exposure",
                "banner",
            ).select_related(
                "restaurant"
            ).get(
                uid=self.kwargs["uid"],
                restaurant_id=user_restaurant.id
            )
            return store

        except AttributeError as e:
            return Store.objects.none()

@extend_schema(
    summary="List and Create Staff for Restaurant Owner",
    methods=["GET", "POST"],
)
class StaffListCreateView(generics.ListCreateAPIView):
    """View for restaurant owner to create or list staff."""
    
    filterset_class = StaffFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StaffCreateSerializer
        return StaffListSerializer

    available_permission_classes = (
        IsRestaurantOwnerUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_queryset(self):
        # Get the restaurant of the logged in restaurant owner
        try:
            user_restaurant = self.request.user.get_restaurant_owner_restaurant

            return (
                RestaurantUser.objects.filter(
                    restaurant=user_restaurant, role=UserKind.RESTAURANT_STAFF
                )
                .select_related("user")
                .only(
                    "user__uid",
                    "user__name",
                    "user__email",
                    "user__image",
                    "user__public_status",
                    "user__username",
                    "user__phone_number",
                )
            )

        except AttributeError as e:
            return RestaurantUser.objects.none()


# class QRCodeGenerationView(APIView):
#     """View to generate QR code for a store and/or staff"""
#
#     available_permission_classes = (
#         IsRestaurantOwnerUser,
#     )
#     permission_classes = (CheckAnyPermission,)
#
#     serializer_class = QRCodeGenerationSerializer
#
#     def post(self, request, *args, **kwargs):
#         """
#         Generate QR code for a store and/or staff.
#         """
#         serializer = self.serializer_class(data=request.data)
#         if not serializer.is_valid():
#             return Response(
#                 serializer.errors,
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Get validated data
#         store_code = serializer.validated_data.get("store_code")
#         staff_username = serializer.validated_data.get("staff_username")
#
#         # Construct the QR code URL based on provided parameters
#         domain = settings.FRONTEND_URL
#         qr_url = domain
#
#         if store_code:
#             qr_url += f"/store/{store_code}"
#             if staff_username:
#                 qr_url += f"/staff/{staff_username}"
#
#         # Generate QR code
#         qr = qrcode.QRCode(
#             version=1,
#             error_correction=qrcode.constants.ERROR_CORRECT_L,
#             box_size=10,
#             border=4,
#         )
#         qr.add_data(qr_url)
#         qr.make(fit=True)
#
#         # Create an in-memory file to store the QR code image
#         img_io = io.BytesIO()
#         qr.make_image(fill_color="black", back_color="white").save(img_io, "PNG")
#         img_io.seek(0)  # Reset the buffer to read from the beginning
#
#         # Return the QR code as a response
#         return HttpResponse(
#             img_io.read(),
#             content_type="image/png",
#             status=status.HTTP_200_OK
#         )


@extend_schema(
        summary="List staff members for a specific store.",
        parameters=[
            OpenApiParameter(
                name='store_code',
                type=str,
                location=OpenApiParameter.QUERY,
                description="The code of the store to list staff members for.",
                required=True
            )
        ],
        responses={200: StaffUserSerializer(many=True)},
    )
class StaffListByStoreView(generics.ListAPIView):
    """View to list staff members by store."""

    serializer_class = StaffUserSerializer
    pagination_class = None

    available_permission_classes = (IsRestaurantOwnerUser,)
    permission_classes = (CheckAnyPermission,)


    def get_queryset(self):
        """Retrieve staff members associated with a specific store."""
        store_code = self.request.query_params.get("store_code", None)
        user_restaurant = self.request.user.get_restaurant_owner_restaurant

        if not store_code:
            # Raising an API-friendly error message
            self.permission_denied(
                self.request, message="store_code is required."
            )

        # Get the store associated with the provided store_code
        store = Store().get_all_actives().filter(
            code=store_code,
            restaurant_id=user_restaurant.id
        ).first()

        if not store:
            self.permission_denied(
                self.request, message="Invalid store_code or store does not exist."
            )

        # Fetch and return staff members for this store
        return StoreUser.objects.filter(
            store=store,
            role=UserKind.RESTAURANT_STAFF,
            user__public_status=PublicStatus.PUBLIC  # Only include public users
        )

@extend_schema(
    summary="Get gacha history statistics for a restaurant's stores.",
)
class RestaurantGachaHistoryView(generics.ListAPIView):
    """View to get gacha history statistics for a restaurant's stores."""

    available_permission_classes = (IsRestaurantOwnerUser,)
    permission_classes = (CheckAnyPermission,)

    serializer_class = GachaHistorySerializer
    pagination_class = None


    def get_queryset(self):
        # Get the restaurant of the logged-in restaurant owner
        restaurant = self.request.user.get_restaurant_owner_restaurant

        # Annotate each store with gacha statistics
        stores = Store.objects.filter(
            restaurant=restaurant
        ).annotate(
            # Annotate gacha enabled status
            gacha_settings=F('gacha_enabled'),

            # Annotate counts for each gacha kind and status
            gold_issued=Count(
                'gacha_store_histories',
                filter=Q(gacha_store_histories__gacha_kind=GachaKind.GOLD) &
                       Q(gacha_store_histories__is_consumed=False)
            ),
            gold_used=Count(
                'gacha_store_histories',
                filter=Q(gacha_store_histories__gacha_kind=GachaKind.GOLD) &
                       Q(gacha_store_histories__is_consumed=True)
            ),
            silver_issued=Count(
                'gacha_store_histories',
                filter=Q(gacha_store_histories__gacha_kind=GachaKind.SILVER) &
                       Q(gacha_store_histories__is_consumed=False)
            ),
            silver_used=Count(
                'gacha_store_histories',
                filter=Q(gacha_store_histories__gacha_kind=GachaKind.SILVER) &
                       Q(gacha_store_histories__is_consumed=True)
            ),
            bronze_issued=Count(
                'gacha_store_histories',
                filter=Q(gacha_store_histories__gacha_kind=GachaKind.BRONZE) &
                       Q(gacha_store_histories__is_consumed=False)
            ),
            bronze_used=Count(
                'gacha_store_histories',
                filter=Q(gacha_store_histories__gacha_kind=GachaKind.BRONZE) &
                       Q(gacha_store_histories__is_consumed=True)
            ),
        ).values(
            'uid',
            'name',
            'banner',
            'gacha_settings',
            'gold_issued',
            'gold_used',
            'silver_issued',
            'silver_used',
            'bronze_issued',
            'bronze_used',
        )

        return stores


@extend_schema(
    summary="Change the restaurant owner's name.",
    methods=["POST"],
)
class RestaurantOwnerChangeNameView(generics.CreateAPIView):
    available_permission_classes = (IsRestaurantOwnerUser,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = ChangeRestaurantOwnerNameSerializer

@extend_schema(
    summary="Get the restaurant owner's detail.",
    methods=["GET"],
)
class RestaurantOwnerDetailView(generics.GenericAPIView):
    available_permission_classes = (IsRestaurantOwnerUser,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = RestaurantOwnerDetailSerializer

    def get(self, request, *args, **kwargs):
        # Assuming the user is the restaurant owner
        user = request.user
        try:
            restaurant = Restaurant.objects.select_related(
                "restaurant_owner"
            ).get(restaurant_owner=user)

            bank_account = BankAccount.objects.select_related(
                "user"
            ).filter(user=user, is_active=True).first()

            # Prepare the data for the serializer
            data = {
                'restaurant': restaurant,
                'bank_account': bank_account
            }

            serializer = self.get_serializer(data)
            return Response(serializer.data)

        except Restaurant.DoesNotExist:
            return Response({"error": "Restaurant not found for this owner."}, status=404)

@extend_schema(
    summary="Get the restaurant owner's reviews [Reviews of Consumers]",
    methods=["GET"],
)
class RestaurantOwnerReviewListView(generics.ListAPIView):
    """
    API view for restaurant owners to list their reviews.
    """
    available_permission_classes = (IsRestaurantOwnerUser,)
    permission_classes = (CheckAnyPermission,)
    pagination_class = None
    serializer_class = RestaurantOwnerReviewListSerializer

    def get_queryset(self):
        # Assuming the user is the restaurant owner
        user = self.request.user
        restaurant = user.get_restaurant_owner_restaurant
        try:
            reviews = Review.objects.filter(
                store_uid__in=[store.uid for store in restaurant.stores.all()]
            )
            return reviews
        except Restaurant.DoesNotExist:
            return Response({"error": "Restaurant not found for this owner."}, status=404)
@extend_schema(
    summary="Create a reply to a review.",
    methods=["POST"],
)
class RestaurantOwnerReplyCreateView(generics.CreateAPIView):
    """
    API view for restaurant owners to create a reply to a review.
    Only a user with the restaurant owner role is allowed to create replies.
    """
    serializer_class = RestaurantOwnerReplySerializer
    available_permission_classes = (IsRestaurantOwnerUser,)
    permission_classes = (CheckAnyPermission,)

    def perform_create(self, serializer):
        serializer.save()

@extend_schema(
    summary="Retrieve a review and its replies.",
    methods=["GET"],
)
class RestaurantOwnerRetrieveReviewRepliesView(generics.RetrieveAPIView):
    available_permission_classes = (IsRestaurantOwnerUser,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = RestaurantOwnerReviewRepliesSerializer

    lookup_url_kwarg = 'review_uid'
    lookup_field = 'uid'

    def get_queryset(self):
        user = self.request.user
        restaurant = user.get_restaurant_owner_restaurant
        return Review.objects.filter(
            store_uid__in=[store.uid for store in restaurant.stores.all()]
        )
