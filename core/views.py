from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer, TokenObtainPairSerializer, \
    TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView, TokenRefreshView

from core.emails import Util
from core.models import Profile, User
from core.serializers import ChangeEmailSerializer, ChangePasswordSerializer, LoginSerializer, ProfileSerializer, \
    RegisterSerializer, RequestEmailChangeCodeSerializer, RequestNewPasswordCodeSerializer, \
    ResendEmailVerificationSerializer, UpdateProfileSerializer, VerifySerializer


# Create your views here.


class ChangeEmailView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangeEmailSerializer

    @extend_schema(
            summary="Change email",
            description=
            """
            This endpoint allows the authenticated user to change their email address after requesting for a code.
            ,
            
            The request should include the following data:

            - `code`: The verification code sent to the user's current email.
            - `email`: The new email address.

            If the email change is successful, the response will include the following data:

            - `message`: A success message indicating that the email has been updated successfully.
            - `status`: The status of the request.
            """

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
            return Response({"message": "Account not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        otp = user.otp.first()
        if otp is None or otp.code is None:
            return Response({"message": "No OTP found for this account", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        elif otp.code != code:
            return Response({"message": "Code is not correct", "status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
        elif otp.expired:
            otp.delete()
            return Response({"message": "Code has expired. Request for another", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        if user.email == new_email:
            return Response({"message": "New email cannot be same as old email", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        user.email = new_email
        user.email_changed = True
        user.is_verified = False
        user.save()
        otp.delete()
        if not user.is_verified:
            Util.email_activation(user)
        return Response(
                {"message": "Email updated successfully. Please check new email for verification", "status": "success"},
                status=status.HTTP_200_OK)


class ChangePasswordView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    @extend_schema(
            summary="Change password",
            description=
            """
            This endpoint allows the authenticated user to change their password after requesting for a code.
            The request should include the following data:

            - `code`: The verification code sent to the user's email.
            - `password`: The new password.

            If the password change is successful, the response will include the following data:

            - `message`: A success message indicating that the password has been updated successfully.
            - `status`: The status of the request.
            """
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
            return Response({"message": "Account not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        otp = user.otp.first()
        if otp is None or otp.code is None:
            return Response({"message": "No OTP found for this account", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        elif otp.code != code:
            return Response({"message": "Code is not correct", "status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
        elif otp.expired:
            otp.delete()
            return Response({"message": "Code has expired. Request for another", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        if user.check_password(password):
            return Response({"message": "New password cannot be same as old password", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        otp.delete()
        return Response({"message": "Password updated successfully", "status": "success"}, status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    @extend_schema(
            summary="Login",
            description=
            """
            This endpoint authenticates a registered and verified user and provides the necessary authentication tokens.
            The request should include the following data:

            - `email`: The user's email address.
            - `password`: The user's password.

            If the login is successful, the response will include the following data:

            - `access`: The access token used for authorization.
            - `refresh`: The refresh token used for obtaining a new access token.
            """

    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({"message": "Invalid credentials", "status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_verified:
            return Response({"message": "Email is not verified", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"message": "Account is not active, contact the admin", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        tokens = super().post(request)

        return Response({"message": "Logged in successfully", "tokens": tokens.data,
                         "data": {"email": user.email, "full_name": user.full_name}, "status": "success"},
                        status=status.HTTP_200_OK)


class LogoutView(TokenBlacklistView):
    serializer_class = TokenBlacklistSerializer

    @extend_schema(
            summary="Logout",
            description=
            """
            This endpoint logs out an authenticated user by blacklisting their access token.
            The request should include the following data:

            - `refresh`: The refresh token used for authentication.

            If the logout is successful, the response will include the following data:

            - `message`: A success message indicating that the user has been logged out.
            - `status`: The status of the request.
            """
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return Response({"message": "Logged out successfully.", "status": "success"}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"message": "Token is blacklisted.", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)


class ListUpdateProfileView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    @extend_schema(
            summary="Get user profile",
            description=
            """
            This endpoint allows an authenticated user to retrieve their profile information.
            If the profile exists, the response will include the following data:

            - `message`: A success message indicating that the profile has been retrieved.
            - `data`: The user's profile information.
            - `status`: The status of the request.
            """
    )
    def get(self, request):
        customer_account = self.request.user
        try:
            customer_profile = Profile.objects.get(user=customer_account)
        except Profile.DoesNotExist:
            return Response({"message": "Profile for this customer account does not exist", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(customer_profile)
        data = serializer.data
        return Response({"message": "Profile retrieved successfully", "data": data, "status": "success"},
                        status=status.HTTP_200_OK)

    @extend_schema(
            summary="Update profile",
            description=
            """
            This endpoint allows an authenticated user to update their profile information.
            The request should include the updated profile data.

            If the profile is successfully updated, the response will include the following data:

            - `message`: A success message indicating that the profile has been updated.
            - `data`: The updated user's profile information.
            - `status`: The status of the request.
            """
    )
    def patch(self, request):
        customer_account = self.request.user
        try:
            customer_profile = Profile.objects.get(user=customer_account)
        except Profile.DoesNotExist:
            return Response({"message": "Profile for this customer account does not exist", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = UpdateProfileSerializer(data=request.data, partial=True, instance=customer_profile)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Split the full_name and updates the first_name and last_name fields
        full_name = serializer.validated_data.get('full_name', '')

        if full_name:
            first_name, *last_name_parts = full_name.split(" ")
            last_name = ' '.join(last_name_parts)
            customer_account.first_name = first_name
            customer_account.last_name = last_name
            customer_account.save()
        data = serializer.data
        return Response({"message": "Profile updated successfully", "data": data, "status": "success"},
                        status=status.HTTP_200_OK)


class RefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer

    @extend_schema(
            summary="Refresh token",
            description=
            """
            This endpoint allows a user to refresh an expired access token.
            The request should include the following data:

            - `access`: The expired access token.

            If the token refresh is successful, the response will include the following data:

            - `message`: A success message indicating that the token has been refreshed.
            - `token`: The new access token.
            - `status`: The status of the request.
            """

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_token = serializer.validated_data['access']
        return Response({"message": "Refreshed successfully", "token": access_token, "status": "success"},
                        status=status.HTTP_200_OK)


class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer

    @extend_schema(
            summary="Registration",
            description=
            """
            This endpoint allows a new user to register an account.
            The request should include the following data:

            - `email`: The user's email address.
            - `first_name`: The user's first name.
            - `last_name`: The user's last name.
            - `password`: The user's password.

            If the registration is successful, the response will include the following data:

            - `message`: A success message indicating that the user has been registered.
            - `status`: The status of the request.
            """

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = serializer.data

        Util.email_activation(user)
        return Response({"message": "Registered successfully. Check email for verification code", "data": data,
                         "status": "success"}, status=status.HTTP_201_CREATED)


class RequestEmailChangeCodeView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = RequestEmailChangeCodeSerializer

    @extend_schema(
            summary="Request email change code",
            description=
            """
            This endpoint allows an authenticated user to request a verification code to change their email address.
            The request should include the following data:

            - `email`: The user's current email address.

            If the request is successful, the response will include the following data:

            - `message`: A success message indicating that the verification code has been sent.
            - `status`: The status of the request.
            """

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Account not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        if user.email_changed is True:
            days_left = (user.is_modified + timedelta(days=10) - timezone.now()).days
            message = f"You can change your email again after {days_left} day(s) because your email has been recently changed."
            return Response({"message": message, "status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
        Util.email_change(user)
        return Response({"message": "Code for email change sent successfully", "status": "success"},
                        status=status.HTTP_200_OK)


class ResendEmailVerificationCodeView(GenericAPIView):
    serializer_class = ResendEmailVerificationSerializer

    @extend_schema(
            summary="Resend email verification code",
            description=
            """
            This endpoint allows a user to request a new verification email for account activation.
            The request should include the following data:

            - `email`: The user's email address.

            If the request is successful, the response will include the following data:

            - `message`: A success message indicating that the verification email has been sent.
            - `status`: The status of the request.
            """

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Account not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        if user.is_verified:
            return Response({"message": "Account already verified. Log in", "status": "success"},
                            status=status.HTTP_200_OK)

        Util.email_activation(user)
        return Response({"message": "Verification code sent successfully", "status": "success"},
                        status=status.HTTP_200_OK)


class RequestNewPasswordCodeView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = RequestNewPasswordCodeSerializer

    @extend_schema(
            summary="Request new password code",
            description=
            """
            This endpoint allows a user to request a verification code to reset their password.
            The request should include the following data:

            - `email`: The user's email address.

            If the request is successful, the response will include the following data:

            - `message`: A success message indicating that the verification code has been sent.
            - `status`: The status of the request.
            """

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Account not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        if not user.is_verified:
            return Response({"message": "Verify your account.", "status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

        Util.password_activation(user)
        return Response({"message": "Password code sent successfully", "status": "success"}, status=status.HTTP_200_OK)


class VerifyEmailView(GenericAPIView):
    serializer_class = VerifySerializer

    @extend_schema(
            summary="Verify email",
            description=
            """
            This endpoint allows a user to verify their account using a verification code.
            The request should include the following data:

            - `code`: The verification code sent to the user's email.

            If the verification is successful, the response will include the following data:

            - `message`: A success message indicating that the account has been verified.
            - `status`: The status of the request.
            """

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
            return Response({"message": "Account not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)

        otp = user.otp.first()
        if otp is None or otp.code is None:
            return Response({"message": "No OTP found for this account", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        elif otp.code != code:
            return Response({"message": "Code is not correct", "status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
        elif otp.expired:
            otp.delete()
            return Response({"message": "Code has expired. Request for another", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        elif user.is_verified:
            otp.delete()
            return Response({"message": "Account already verified. Log in", "status": "success"},
                            status=status.HTTP_200_OK)

        user.is_verified = True
        otp.delete()
        if not user.email_changed:
            Util.email_verified(user)
        user.save()
        return Response({"message": "Account verified successfully", "status": "success"}, status=status.HTTP_200_OK)
