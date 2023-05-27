import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.urls import reverse_lazy
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from core.models import Otp
from store.models import Product


class AuthenticationTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Product = Product.objects.all()
        cls.User = get_user_model()

    def setUp(self):
        self.code = random.randint(1000, 9999)
        self.expiry_date = timezone.now() + timedelta(minutes=15)
        self.store_data = {}
        self.user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "lookouttest91@zohomail.com",
            "password": "string",
        }
        self.second_user_data = {
            "first_name": "Smith",
            "last_name": "Doe",
            "email": "loplo1@gmail.com",
            "password": "string",
        }
        self.address_data = {
            "country": "US",
            "first_name": "Smith",
            "last_name": "Damian",
            "street_address": "Denmark ville, close to the port",
            "second_street_address": "",
            "city": "America",
            "state": "United States",
            "zip_code": "678774",
            "phone_number": "+09873778282"
        }
        self.client = APIClient()

    def tearDown(self):
        self.Product.all().delete()
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

    def test_user_can_register_with_data(self):
        self._register_user()

    def test_user_can_register_with_data_and_authenticate_with_correct_verification_code(self):
        self._register_user()
        self._verify_email()

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

    def test_create_user_address(self):
        self._authenticate_user()
        response = self.client.post(reverse_lazy("address"), data=self.address_data, format="json")
        self.created_address = response.data.get('data').get('id')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_all_user_address(self):
        self._authenticate_user()
        response = self.client.get(reverse_lazy("address"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_specific_user_address(self):
        self._authenticate_user()
        self.test_create_user_address()
        param = {"address_param": self.created_address}
        response = self.client.get(reverse_lazy("address"), data=param)
        print(response, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

