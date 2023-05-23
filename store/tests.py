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