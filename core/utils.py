from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core.oauth_serializers import GoogleSocialAuthSerializer


class GoogleSocialAuthView(GenericAPIView):
    serializer_class = GoogleSocialAuthSerializer

    @extend_schema(
            summary="Google Authentication Endpoint",
            description="This endpoint allows users to authenticate through Google",
            request=GoogleSocialAuthSerializer,
            responses={
                200: "Success.",
                404: "Account not found.",
                500: "Internal server error."
            }

    )
    def post(self, request):
        """
        POST with "auth token"

        Send an id_token as from Google to get user information

        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = (serializer.validated_data['auth_token'])
        return Response(data, status=status.HTTP_200_OK)
