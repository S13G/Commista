from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from store.models import Product


class AuthenticationTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Product = Product.objects.all()
        cls.User = get_user_model()

    def setUp(self):
        self.store_data = {}
        client = APIClient()

    def tearDown(self):
        self.Product.objects.all().delete()
        self.User.objects.all().delete()

    def test_get_all_user_address(self):
        pass