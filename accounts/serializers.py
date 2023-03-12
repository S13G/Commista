from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from accounts.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=50, min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password']

    def validate(self, attrs):
        email = attrs.get('email', '')
        full_name = attrs.get('full_name', '')

        # validate email
        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError("Invalid email format")

        # validate full_name
        if not full_name:
            raise serializers.ValidationError("Full name is required")
        elif len(full_name.split()) != 2:
            raise serializers.ValidationError("Full name must be two words")

        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)