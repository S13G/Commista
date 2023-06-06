import re

from django.core.validators import FileExtensionValidator
from django.core.validators import validate_email
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.choices import GENDER_CHOICES
from core.models import User


class ChangeEmailSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    email = serializers.EmailField()

    def validate(self, attrs):
        code = attrs.get('code')
        email = attrs.get('email')

        if not code:
            raise serializers.ValidationError({"message": "Code is required", "status": "failed"})

        if not re.match("^[0-9]{4}$", str(code)):
            raise serializers.ValidationError({"message": "Code must be 4-digit number", "status": "failed"})

        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError({"message": "Invalid email format", "status": "failed"})

        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    password = serializers.CharField(max_length=50, min_length=6, write_only=True)

    def validate(self, attrs):
        code = attrs.get('code')

        if not code:
            raise serializers.ValidationError({"message": "Code is required", "status": "failed"})

        if not re.match("^[0-9]{4}$", str(code)):
            raise serializers.ValidationError({"message": "Code must be 4-digit number", "status": "failed"})

        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=150, min_length=6, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError({"message": "Invalid email format", "status": "failed"})

        return attrs


class ProfileSerializer(serializers.Serializer):
    email = serializers.EmailField(source="user.email")
    full_name = serializers.CharField(source="user.full_name")
    gender = serializers.ChoiceField(choices=GENDER_CHOICES)
    birthday = serializers.DateField()
    phone_number = serializers.CharField(max_length=20)
    _avatar = serializers.ImageField(validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])

    def validate__avatar(self, attrs):
        avatar = attrs.get('_avatar')
        max_size = 5 * 1024 * 1024  # 3MB in bytes
        if avatar.size > max_size:
            raise ValidationError({"message": f"Image {avatar} size should be less than 5MB", "status": "failed"})
        return attrs

    def validate_phone_number(self, value):
        phone_number = value
        if not phone_number.startswith('+'):
            raise ValidationError({"message": "Phone number must start with a plus sign (+)", "status": "failed"})
        if not phone_number[1:].isdigit():
            raise ValidationError(
                    {"message": "Phone number must only contain digits after the plus sign (+)", "status": "failed"})
        return value


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=50, min_length=6, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        first_name = attrs.get('first_name')
        last_name = attrs.get('last_name')

        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError({"message": "Invalid email format", "status": "failed"})

        if not first_name:
            raise serializers.ValidationError({"message": "First name is required", "status": "failed"})
        if not last_name:
            raise serializers.ValidationError({"message": "Last name is required", "status": "failed"})

        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class RequestEmailChangeCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError({"message": "Invalid email format", "status": "failed"})
        return attrs


class ResendEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError({"message": "Invalid email format", "status": "failed"})
        return attrs


class RequestNewPasswordCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError({"message": "Invalid email format", "status": "failed"})
        return attrs


class UpdateProfileSerializer(serializers.Serializer):
    _avatar = serializers.ImageField(validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    birthday = serializers.DateField()
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(max_length=255)
    gender = serializers.ChoiceField(choices=GENDER_CHOICES)
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        phone_number = value
        if not phone_number.startswith('+'):
            raise ValidationError({"message": "Phone number must start with a plus sign (+)", "status": "failed"})
        if not phone_number[1:].isdigit():
            raise ValidationError(
                    {"message": "Phone number must only contain digits after the plus sign (+)", "status": "failed"})
        return value

    def validate__avatar(self, attrs):
        avatar = attrs.get('_avatar')
        max_size = 5 * 1024 * 1024  # 3MB in bytes
        if avatar.size > max_size:
            raise ValidationError({"message": f"Image {avatar} size should be less than 5MB", "status": "failed"})
        return attrs

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
            instance.save()
        return instance


class VerifySerializer(serializers.Serializer):
    code = serializers.IntegerField()
    email = serializers.EmailField()

    def validate(self, attrs):
        code = attrs.get('code')
        email = attrs.get('email')

        if not code:
            raise serializers.ValidationError({"message": "Code is required", "status": "failed"})

        if not re.match("^[0-9]{4}$", str(code)):
            raise serializers.ValidationError({"message": "Code must be a 4-digit number", "status": "failed"})

        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError({"message": "Invalid email format", "status": "failed"})

        return attrs
