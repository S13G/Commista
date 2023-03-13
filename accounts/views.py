from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.auth import CustomHeaderAuthentication
from accounts.emails import Util
from accounts.models import User
from accounts.serializers import LoginSerializer, RegisterSerializer, VerifySerializer


# Create your views here.


class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
    authentication_classes = [CustomHeaderAuthentication]

    def post(self, request, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # use validated_data when you want to so any operation with the data like authenticate
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({"message": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_verified:
            return Response({"message": "Email is not verified"}, status=status.HTTP_400_BAD_REQUEST)

        tokens = super().post(request)
        return Response({"message": "Logged in successfully", "tokens": tokens.data}, status=status.HTTP_200_OK)


class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        data = serializer.data

        Util.email_activation(user)
        return Response({"message": "Registered successfully. Check email for verification code", "data": data},
                        status=status.HTTP_201_CREATED)


class VerifyEmailView(GenericAPIView):
    serializer_class = VerifySerializer

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
            otp.code = None  # set it to null in the admin
            otp.save()
            return Response({"message": "Code has expired"}, status=status.HTTP_400_BAD_REQUEST)
        elif user.is_verified:
            otp.delete()
            return Response({"message": "Account already verified. Log in"}, status=status.HTTP_200_OK)

        user.is_verified = True
        otp.delete()
        if not user.email_changed:
            Util.email_verified(user)
        user.save()
        return Response({"message": "Account verified successfully"}, status=status.HTTP_200_OK)

