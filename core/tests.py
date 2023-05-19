import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.urls import reverse_lazy
from django.utils import timezone
from faker import Faker
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from core.models import Otp


class AuthenticationTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fake = Faker()
        cls.User = get_user_model()

    def setUp(self):
        self.code = random.randint(1000, 9999)
        self.expiry_date = timezone.now() + timedelta(minutes=15)
        self.user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "lookouttest91@zohomail.com",
            "password": "string",
        }
        self.client = APIClient()

    def tearDown(self):
        self.User.objects.all().delete()

    def _register_user(self):
        response = self.client.post(reverse_lazy("register"), self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user = self.User.objects.get()
        self.generated_code = Otp.objects.create(
                user=self.user, code=self.code, expiry_date=self.expiry_date
        )

    def _verify_email(self):
        verification_data = {"email": self.user.email, "code": self.generated_code.code}
        response = self.client.post(reverse_lazy("verify_email"), verification_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def _request_otp(self, url_name, data):
        response = self.client.post(reverse_lazy(url_name), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def _change_email_or_password(self, url_name, code_field, new_value):
        user = self.user
        generated_code = Otp.objects.create(user=user, code=self.code, expiry_date=self.expiry_date)
        data = {"code": generated_code.code, code_field: new_value}
        response = self.client.post(reverse_lazy(url_name), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_register_without_data(self):
        response = self.client.post(reverse_lazy("register"), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_register_with_data(self):
        self._register_user()

    def test_user_can_register_with_data_and_cannot_authenticate_with_incorrect_verification_code(self):
        self._register_user()
        response = self.client.post(reverse_lazy("verify_email"), {"code": "2001"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_register_with_data_and_authenticate_with_correct_verification_code(self):
        self._register_user()
        self._verify_email()

    def test_send_user_new_verification_code(self):
        self._register_user()
        self._request_otp("resend_verification_code", {"email": self.user.email})

    def test_user_cannot_login_with_unverified_email(self):
        self._register_user()
        response = self.client.post(
                reverse_lazy("login"), {"email": self.user.email, "password": self.user.password}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_login_with_verified_email(self):
        self._register_user()
        self._verify_email()

        user = self.user
        login_data = {"email": user.email, "password": self.user_data["password"]}
        if check_password(self.user_data["password"], user.password):
            response = self.client.post(reverse_lazy("login"), login_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.logout_user_response = response
            self.login_response = self.User.objects.get()

    def _authenticate_user(self):
        self.test_user_can_login_with_verified_email()
        user = self.login_response
        token = Token.objects.create(user=user)
        self.client.force_authenticate(user=user, token=token.key)

    def test_unauthenticated_user_cannot_request_email_change_code(self):
        response = self.client.post(reverse_lazy("request_email_change_code"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_without_token_cannot_request_email_change_code(self):
        self.test_user_can_login_with_verified_email()
        email = self.user.email
        response = self.client.post(reverse_lazy("request_email_change_code"), {"email": email}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_with_token_can_request_email_change_code(self):
        self._authenticate_user()
        email = self.user.email
        response = self.client.post(reverse_lazy("request_email_change_code"), {"email": email}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_user_cannot_change_email_with_incorrect_code(self):
        self._authenticate_user()
        new_email = self.fake.email()
        response = self.client.post(
                reverse_lazy("change_email"), {"code": 1234, "email": new_email}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_user_can_change_email_with_correct_code(self):
        self._authenticate_user()
        new_email = self.fake.email()
        self._change_email_or_password("change_email", "email", new_email)

    def test_unauthenticated_user_cannot_request_password_change_code(self):
        response = self.client.post(reverse_lazy("request_password_code"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_without_token_cannot_request_password_change_code(self):
        self.test_user_can_login_with_verified_email()
        email = self.user.email
        response = self.client.post(reverse_lazy("request_password_code"), {"email": email}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_with_token_can_request_password_change_code(self):
        self._authenticate_user()
        email = self.user.email
        response = self.client.post(reverse_lazy("request_password_code"), {"email": email}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_user_cannot_change_password_with_incorrect_code(self):
        self._authenticate_user()
        new_password = random.randint(100000, 999999)
        response = self.client.post(
                reverse_lazy("change_password"), {"code": 1234, "password": new_password}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_user_can_change_password_with_correct_code(self):
        self._authenticate_user()
        new_password = random.randint(100000, 999999)
        self._change_email_or_password("change_password", "password", new_password)

    def test_logout_user(self):
        self._authenticate_user()
        refresh_token = self.logout_user_response.data["tokens"]["refresh"]
        access_token = self.logout_user_response.data["tokens"]["access"]
        data = {"refresh": refresh_token, "token": access_token}
        response = self.client.post(reverse_lazy("logout"), data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user_profile(self):
        self._authenticate_user()
        response = self.client.get(reverse_lazy("list_update_profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_profile(self):
        self._authenticate_user()
        updated_data = {
            "full_name": "Matir Mani",
            "gender": "F",
            "birthday": "2023-05-12",
            "phone_number": "+123131331321"
        }
        response = self.client.patch(reverse_lazy("list_update_profile"), data=updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
