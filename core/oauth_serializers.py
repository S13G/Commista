from abc import ABC, ABCMeta

from decouple import config
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from core import google
from core.oauth_funcs import register_social_user


class GoogleSocialAuthSerializer(serializers.Serializer):
    auth_token = serializers.CharField()

    @staticmethod
    def validate_auth_token(auth_token):
        user_data = google.Google.validate(auth_token)
        try:
            user_data["sub"]
        except:
            raise serializers.ValidationError("The token is invalid or expired, please login again.")

        if user_data['aud'] != config('GOOGLE_CLIENT_ID'):
            raise AuthenticationFailed("Invalid client ID. Please try again with the correct Google client ID.")

        user_id = user_data["sub"]
        email = user_data["email"]
        name = user_data["name"]
        provider = 'google'

        return register_social_user(provider=provider, user_id=user_id, email=email, name=name)
