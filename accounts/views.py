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
        email = serializer.data["email"]
        code = serializer.data["code"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        if user.otp.code != code:
            return Response({"message": "Code is not correct"}, status=status.HTTP_400_BAD_REQUEST)
        elif user.otp.expired:
            user.otp.code = None
            user.otp.save()
            return Response({"message": "Code has expired"}, status=status.HTTP_400_BAD_REQUEST)
        elif user.is_verified:
            return Response({"message": "Account already verified. Log in"}, status=status.HTTP_200_OK)

        user.is_verified = True
        user.otp.code = None
        user.otp.save()
        if not user.email_changed:
            Util.email_verified(user)
        user.save()
        return Response({"message": "Account verified successfully"}, status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
    authentication_classes = [CustomHeaderAuthentication]

    def post(self, request, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.data["email"]
        password = serializer.data["password"]
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({"message": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_verified:
            return Response({"message": "Email is not verified"}, status=status.HTTP_400_BAD_REQUEST)

        tokens = super().post(request)
        return Response({"message": "Logged in successfully", "tokens": tokens.data}, status=status.HTTP_200_OK)
