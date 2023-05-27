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
from store.models import Category, Colour, ColourInventory, Product, ProductImage, Size, SizeInventory


class AuthenticationTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Product = Product.objects.all()
        cls.Category = Category.objects.all()
        cls.User = get_user_model()

    def setUp(self):
        self.code = random.randint(1000, 9999)
        self.expiry_date = timezone.now() + timedelta(minutes=15)

        self.category_data = [
            {
                "title": "Fashion",
                "gender": "A"
            },
            {
                "title": "Toys",
                "gender": "K"
            }
        ]
        self.first_category = Category.objects.create(**self.category_data[0])
        self.second_category = Category.objects.create(**self.category_data[1])

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

        self.updated_address_data = {
            "country": "AF",
            "first_name": "Domino",
            "last_name": "Daanny",
            "street_address": "Denark ville, close to the port",
            "second_street_address": "",
            "city": "Austria",
            "state": "England",
            "zip_code": "678774",
            "phone_number": "+43987377232"
        }

        # create colour instances
        self.colour_data = [
            {
                "name": "Red",
                "hex_code": "#979721"
            },
            {
                "name": "Blue",
                "hex_code": "#232453"
            }
        ]

        for colour in self.colour_data:
            Colour.objects.create(**colour)

        self.size_data = [
            {
                "title": "S"
            },
            {
                "title": "M"
            },
            {
                "title": "L"
            }
        ]

        for size in self.size_data:
            Size.objects.create(**size)

        self.colour_inventory_data = [
            {
                "colour": "Red",
                "quantity": 50,
                "extra_price": 2.99
            },
            {
                "colour": "Blue",
                "quantity": 30,
                "extra_price": 0
            }
        ]

        self.size_inventory_data = [
            {
                "size": "S",
                "quantity": 20,
                "extra_price": 0
            },
            {
                "size": "M",
                "quantity": 30,
                "extra_price": 1.99
            },
            {
                "size": "L",
                "quantity": 50,
                "extra_price": 1.99
            }
        ]

        self.colour_inventory = []
        self.size_inventory = []

        # Create the ColourInventory instances
        for color_data in self.colour_inventory_data:
            self.color = ColourInventory.objects.create(**color_data)
            self.colour_inventory.append(self.color)

        # Create the SizeInventory instances
        for size_data in self.size_inventory_data:
            self.size = SizeInventory.objects.create(**size_data)
            self.size_inventory.append(self.size)

        self.first_product_data = {
            "title": "Product 1",
            "slug": "product-1",
            "category": self.first_category,
            "description": "Product 1 description",
            "style": "Product 1 style",
            "price": 19.99,
            "shipped_out_days": 2,
            "shipping_fee": 5.99,
            "inventory": 100,
            "percentage_off": 10,
            "condition": "N",
            "location": "United States",
            "flash_sale_start_date": "",
            "flash_sale_end_date": "",
        }

        # Assign the related objects using set()
        self.first_product = Product.objects.create(**self.first_product_data)
        self.first_product.color_inventory.set(self.colour_inventory)
        self.first_product.size_inventory.set(self.size_inventory)

        # Add the images
        self.images = [
            {
                "image": "store/product_images/product1_image1.jpg"
            },
            {
                "image": "store/product_images/product1_image2.jpg"
            }
        ]

        for img_data in self.images:
            ProductImage.objects.create(product=self.first_product, **img_data)

        self.client = APIClient()

    def tearDown(self):
        self.Category.delete()
        self.Product.delete()
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
        self.test_create_user_address()
        param = {"address_param": self.created_address}
        response = self.client.get(reverse_lazy("address"), data=param)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def _specific_user_address(self):
        self.test_create_user_address()
        address_id = self.created_address
        url = reverse_lazy("address_details", kwargs={"address_id": address_id})
        return url

    def test_update_specific_user_address(self):
        url = self._specific_user_address()
        response = self.client.patch(url, data=self.updated_address_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_delete_specific_user_address(self):
        url = self._specific_user_address()
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_categories(self):
        self._authenticate_user()
        response = self.client.get(reverse_lazy("category_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify the response data structure
        data = response.data
        self.assertIn("message", data)
        self.assertIn("all_categories", data)
        self.assertIn("men_categories", data)
        self.assertIn("women_categories", data)
        self.assertIn("kids_categories", data)
        self.assertIn("status", data)

        # Verify the response message
        self.assertEqual(data["message"], "All categories fetched")
        self.assertEqual(data['status'], "success")

    def test_get_categories_sales(self):
        self._authenticate_user()
        response = self.client.get(reverse_lazy("category_product_sales"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('status', response.data)

        data = response.data['data']
        self.assertIn('categories', data)
        self.assertIn('product_without_flash_sales', data)
        self.assertIn('products_with_flash_sales', data)
        self.assertIn('mega_sales', data)

        self.assertEqual(response.data['message'], "Fetched all products")
        self.assertEqual(response.data['status'], "success")

    def test_add_user_favorite_product(self):
        self._authenticate_user()
        product_id = self.first_product.id
        print(product_id)
        response = self.client.post(reverse_lazy("favorite_product", kwargs={"product_id": product_id}))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['message'], "Product added to favorites")
