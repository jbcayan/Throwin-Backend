"""Views for user"""
from rest_framework.response import Response
from accounts.rest.serializers.user import UserNameSerializer
from rest_framework import generics, status
from drf_spectacular.utils import extend_schema
from common.permissions import IsConsumerUser


@extend_schema(request=UserNameSerializer)
class UserName(generics.CreateAPIView):
    """View for set name for existing user"""

    serializer_class = UserNameSerializer
    permission_classes = [IsConsumerUser]

    def post(self, request, *args, **kwargs):
        print("="*30)
        print(request.data)
        print(request.user)
        print("="*30)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "detail": "User Name Updated Successfully",
            },
            status=status.HTTP_200_OK,
        )
