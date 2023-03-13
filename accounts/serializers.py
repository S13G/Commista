import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from accounts.models import User


class ChangeEmailSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    email = serializers.EmailField()

    def validate(self, attrs):
        code = attrs.get('code', '')
        email = attrs.get('email', '')

        # validate code
        if not code:
            raise serializers.ValidationError("Code is required")

        if not re.match("^[0-9]{4}$", str(code)):
            raise serializers.ValidationError("Code must be a 4-digit number")

        # validate email
        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError("Invalid email format")

        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    password = serializers.CharField(max_length=50, min_length=6, write_only=True)

    def validate(self, attrs):
        code = attrs.get('code', '')

        # validate code
        if not code:
            raise serializers.ValidationError("Code is required")

        if not re.match("^[0-9]{4}$", str(code)):
            raise serializers.ValidationError("Code must be a 4-digit number")

        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=50, min_length=6, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '')

        # validate email
        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError("Invalid email format")

        return attrs


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(max_length=50, min_length=6, write_only=True)

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


class RequestEmailChangeCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get('email', '')

        # validate email
        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError("Invalid email format")
        return attrs


class RequestNewPasswordCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get('email', '')

        # validate email
        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError("Invalid email format")
        return attrs


class ResendEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get('email', '')

        # validate email
        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError("Invalid email format")
        return attrs


class VerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.IntegerField()

    def validate(self, attrs):
        email = attrs.get('email', '')
        code = attrs.get('code', '')

        # validate email
        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError("Invalid email format")

        # validate code
        if not code:
            raise serializers.ValidationError("Code is required")

        if not re.match("^[0-9]{4}$", str(code)):
            raise serializers.ValidationError("Code must be a 4-digit number")

        return attrs
