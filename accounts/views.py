from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer, TokenObtainPairSerializer, \
    TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView, TokenRefreshView

from accounts.emails import Util
from accounts.models import User
from accounts.serializers import ChangeEmailSerializer, ChangePasswordSerializer, LoginSerializer, RegisterSerializer, \
    RequestEmailChangeCodeSerializer, RequestNewPasswordCodeSerializer, ResendEmailVerificationSerializer, \
    VerifySerializer


# Create your views here.


class ChangeEmailView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangeEmailSerializer

    @extend_schema(
            summary="Change Email Endpoint",
            description="This endpoint allows the authenticated user to change their email address after requesting for a code",
            request=ChangeEmailSerializer,
            responses={
                200: "Email updated successfully. Please check new email for verification",
                400: "Invalid request or code has expired",
                401: "Unauthorized. Authentication credentials were not provided.",
                404: "Account not found.",
                500: "Internal server error."
            }

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.user.email
        code = serializer.validated_data['code']
        new_email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        otp = user.otp.first()
        if otp is None or otp.code is None:
            return Response({"message": "No OTP found for this account"}, status=status.HTTP_400_BAD_REQUEST)
        elif otp.code != code:
            return Response({"message": "Code is not correct"}, status=status.HTTP_400_BAD_REQUEST)
        elif otp.expired:
            otp.delete()
            return Response({"message": "Code has expired. Request for another"}, status=status.HTTP_400_BAD_REQUEST)

        if user.email == new_email:
            return Response({"message": "New email cannot be same as old email"},
                            status=status.HTTP_400_BAD_REQUEST)

        user.email = new_email
        user.email_changed = True
        user.is_verified = False
        user.save()
        otp.delete()
        if not user.is_verified:
            Util.email_activation(user)
        return Response({"message": "Email updated successfully. Please check new email for verification"},
                        status=status.HTTP_200_OK)


class ChangePasswordView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @extend_schema(
            summary="Change Password Endpoint",
            description="This endpoint allows the authenticated user to change their password after requesting for a code",
            request=ChangePasswordSerializer,
            responses={
                200: "Password updated successfully.",
                400: "Invalid request or code has expired or not found",
                401: "Unauthorized. Authentication credentials were not provided.",
                404: "Account not found.",
                500: "Internal server error."
            }

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.user.email
        code = serializer.validated_data['code']
        password = serializer.validated_data['password']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        otp = user.otp.first()
        if otp is None or otp.code is None:
            return Response({"message": "No OTP found for this account"}, status=status.HTTP_400_BAD_REQUEST)
        elif otp.code != code:
            return Response({"message": "Code is not correct"}, status=status.HTTP_400_BAD_REQUEST)
        elif otp.expired:
            otp.delete()
            return Response({"message": "Code has expired. Request for another"}, status=status.HTTP_400_BAD_REQUEST)

        if user.check_password(password):
            return Response({"message": "New password cannot be same as old password"},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        otp.delete()
        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    @extend_schema(
            summary="Login Endpoint",
            description="This endpoint logs in a user",
            request=LoginSerializer,
            responses={
                200: "Password updated successfully.",
                400: "Email not verified or Invalid Credentials",
                401: "Unauthorized. Authentication credentials were not provided.",
                404: "Account not found.",
                500: "Internal server error."
            }

    )
    def post(self, request, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # use validated_data when you want to so any operation with the data like authenticate
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_verified:
            return Response({"message": "Email is not verified"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"message": "Account is not active, contact the admin"}, status=status.HTTP_400_BAD_REQUEST)
        tokens = super().post(request)
        return Response({"message": "Logged in successfully", "tokens": tokens.data,
                         "data": {"email": user.email, "full_name": user.full_name}}, status=status.HTTP_200_OK)


class LogoutView(TokenBlacklistView):
    serializer_class = TokenBlacklistSerializer

    @extend_schema(
            summary="Logout Endpoint",
            description="This endpoint logs out an authenticated user.",
            request=TokenBlacklistSerializer,
            responses={
                200: "Logged out successfully.",
                500: "Internal server error."
            }

    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


class RefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer

    @extend_schema(
            summary="Refresh token Endpoint",
            description="This endpoint refreshes an access token",
            request=TokenRefreshSerializer,
            responses={
                200: "Refreshed successfully.",
                500: "Internal server error."
            }

    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_token = serializer.validated_data['access']
        return Response({"message": "Refreshed successfully", "token": access_token}, status=status.HTTP_200_OK)


class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer

    @extend_schema(
            summary="Register Endpoint",
            description="This endpoint registers a new user.",
            request=RegisterSerializer,
            responses={
                200: "Registered successfully. Check email for verification code.",
                500: "Internal server error."
            }

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        data = serializer.data

        Util.email_activation(user)
        return Response({"message": "Registered successfully. Check email for verification code", "data": data},
                        status=status.HTTP_201_CREATED)


class ResendEmailVerificationView(GenericAPIView):
    serializer_class = ResendEmailVerificationSerializer

    @extend_schema(
            summary="Resend Email Verification Code Endpoint",
            description="This endpoint sends a new user a new code to verify if previous code faced issues",
            request=ResendEmailVerificationSerializer,
            responses={
                200: "Verification code sent successfully or Account already Verified.",
                404: "Account not found.",
                500: "Internal server error."
            }

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        if user.is_verified:
            return Response({"message": "Account already verified. Log in"}, status=status.HTTP_200_OK)

        Util.email_activation(user)
        return Response({"message": "Verification code sent successfully"}, status=status.HTTP_200_OK)


class RequestEmailChangeCodeView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RequestEmailChangeCodeSerializer

    @extend_schema(
            summary="Request Email Change code Endpoint",
            description="This endpoint allows the authenticated user to request for a code to change their email",
            request=RequestEmailChangeCodeSerializer,
            responses={
                200: "Code for email change sent successfully.",
                401: "Unauthorized. Authentication credentials were not provided.",
                404: "Account not found.",
                500: "Internal server error."
            }

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        Util.email_change(user)
        return Response({"message": "Code for email change sent successfully"}, status=status.HTTP_200_OK)


class RequestNewPasswordCodeView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RequestNewPasswordCodeSerializer

    @extend_schema(
            summary="Request New Password Endpoint",
            description="This endpoint allows the authenticated user to request for a code to change password",
            request=RequestNewPasswordCodeSerializer,
            responses={
                200: "Password code sent successfully.",
                400: "Verify your account",
                401: "Unauthorized. Authentication credentials were not provided.",
                404: "Account not found.",
                500: "Internal server error."
            }

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        if not user.is_verified:
            return Response({"message": "Verify your account."}, status=status.HTTP_400_BAD_REQUEST)

        Util.password_activation(user)
        return Response({"message": "Password code sent successfully"}, status=status.HTTP_200_OK)


class VerifyEmailView(GenericAPIView):
    serializer_class = VerifySerializer

    @extend_schema(
            summary="Verify Email Endpoint",
            description="This endpoint allows a user to verify their email with the code received",
            request=VerifySerializer,
            responses={
                200: "Account verified successfully.",
                400: "Invalid request or code has expired or not found",
                401: "Unauthorized. Authentication credentials were not provided.",
                404: "Account not found.",
                500: "Internal server error."
            }

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # use request.data.get to get the fields and remove validation in serializer and do your validation in the views
        email = request.data.get("email")
        code = request.data.get("code")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        otp = user.otp.first()
        if otp is None or otp.code is None:
            return Response({"message": "No OTP found for this account"}, status=status.HTTP_400_BAD_REQUEST)
        elif otp.code != code:
            return Response({"message": "Code is not correct"}, status=status.HTTP_400_BAD_REQUEST)
        elif otp.expired:
            otp.delete()
            return Response({"message": "Code has expired. Request for another"}, status=status.HTTP_400_BAD_REQUEST)
        elif user.is_verified:
            otp.delete()
            return Response({"message": "Account already verified. Log in"}, status=status.HTTP_200_OK)

        user.is_verified = True
        otp.delete()
        if not user.email_changed:
            Util.email_verified(user)
        user.save()
        return Response({"message": "Account verified successfully"}, status=status.HTTP_200_OK)
