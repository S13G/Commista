import random

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Otp

User = get_user_model()


class Authentication(APITestCase):
    def setUp(self):
        self.registration_url = reverse("register")
        self.login_url = reverse("login")
        self.verify_email = reverse("verify_email")

        self.user_data = {
            "full_name": "John Doe",
            "email": "lookouttest91@zohomail.com",
            "password": "string"
        }

    def test_user_cannot_register_without_data(self):
        response = self.client.post(self.registration_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_register_with_data(self):
        registration_response = self.client.post(self.registration_url, self.user_data, format="json")
        self.assertEqual(registration_response.status_code, status.HTTP_201_CREATED)
        self.registration_response = registration_response  # store the response to be accessed by others

    def test_user_can_register_with_data_and_cannot_authenticate_with_incorrect_verification_code(self):
        self.test_user_can_register_with_data()
        # verify email
        verification_data = {"code": "2001"}
        verification_response = self.client.post(self.verify_email, verification_data, format="json")
        self.assertEqual(verification_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_register_with_data_and_authenticate_with_correct_verification_code(self):
        self.test_user_can_register_with_data()

        # verify email
        user = User.objects.get(email=self.registration_response.data["data"]["email"])
        code = Otp.objects.create(user=user, code=random.randint(1000, 9999),
                                  expiry_date=timezone.now() + timezone.timedelta(minutes=15))
        verification_data = {"email": user.email, "code": code.code}
        verification_response = self.client.post(self.verify_email, verification_data, format="json")
        self.assertEqual(verification_response.status_code, status.HTTP_200_OK)
        self.user = user  # store the user

    def test_user_cannot_login_with_unverified_email(self):
        self.test_user_can_register_with_data()
        user = User.objects.get(email=self.registration_response.data["data"]["email"])
        login_data = {"email": user.email, "password": user.password}
        response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_login_with_verified_email_and_get_token_credentials(self):
        self.test_user_can_register_with_data_and_authenticate_with_correct_verification_code()
        user = self.user
        login_data = {"email": user.email, "password": self.user_data["password"]}
        if check_password(self.user_data["password"], user.password):
            response = self.client.post(self.login_url, login_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
