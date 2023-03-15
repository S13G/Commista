import random

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.utils import timezone
from faker import Faker
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from accounts.models import Otp


class Authentication(APITestCase):
    def setUp(self):
        # URLs
        self.change_email = reverse("change_email")
        self.change_password = reverse("change_password")
        self.registration_url = reverse("register")
        self.email_change_code = reverse("request_email_change_code")
        self.login_url = reverse("login")
        self.password_change_code = reverse("request_password_code")
        self.resend_verification_code = reverse("resend_verification_code")
        self.verify_email = reverse("verify_email")
        self.logout = reverse("logout")

        # values
        self.code = random.randint(1000, 9999)
        self.fake = Faker()
        self.expiry_date = timezone.now() + timezone.timedelta(minutes=15)
        self.user_data = {
            "full_name": "John Doe",
            "email": "lookouttest91@zohomail.com",
            "password": "string"
        }
        self.token_client = APIClient()
        self.User = get_user_model()

    def test_user_cannot_register_without_data(self):
        response = self.client.post(self.registration_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_register_with_data(self):
        registration_response = self.client.post(self.registration_url, self.user_data, format="json")
        self.assertEqual(registration_response.status_code, status.HTTP_201_CREATED)
        # Below are variables being used by other functions
        self.user = self.User.objects.get(email=registration_response.data["data"]["email"])
        self.generated_code = Otp.objects.create(user=self.user, code=self.code, expiry_date=self.expiry_date)

    def test_user_can_register_with_data_and_cannot_authenticate_with_incorrect_verification_code(self):
        self.test_user_can_register_with_data()
        # verify email
        verification_data = {"code": "2001"}
        verification_response = self.client.post(self.verify_email, verification_data, format="json")
        self.assertEqual(verification_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_register_with_data_and_authenticate_with_correct_verification_code(self):
        self.test_user_can_register_with_data()

        # verify email
        user = self.user
        verification_data = {"email": user.email, "code": self.generated_code.code}
        verification_response = self.client.post(self.verify_email, verification_data, format="json")
        self.assertEqual(verification_response.status_code, status.HTTP_200_OK)

    def test_send_user_new_verification_code(self):
        self.test_user_can_register_with_data()
        user = self.user
        resend_verification_code_response = self.client.post(self.resend_verification_code, {"email": user.email},
                                                             format="json")
        self.assertEqual(resend_verification_code_response.status_code, status.HTTP_200_OK)

    def test_user_cannot_login_with_unverified_email(self):
        self.test_user_can_register_with_data()
        user = self.user
        login_data = {"email": user.email, "password": user.password}
        response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_login_with_verified_email(self):
        self.test_user_can_register_with_data_and_authenticate_with_correct_verification_code()
        user = self.user
        login_data = {"email": user.email, "password": self.user_data["password"]}
        if check_password(self.user_data["password"], user.password):
            response = self.client.post(self.login_url, login_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Below are values used by others
            self.logout_user_response = response
            self.login_response = self.User.objects.get(email=response.data["data"]["email"])

    def test_get_authenticated_user_token_credentials(self):
        self.test_user_can_login_with_verified_email()
        user = self.login_response
        token = Token.objects.create(user=user)
        self.token_client.force_authenticate(user=user, token=token.key)

    def test_unauthenticated_user_cannot_request_for_email__change_code(self):
        response = self.client.post(self.email_change_code, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_without_token_credentials_cannot_request_for_email_change_code(self):
        self.test_user_can_login_with_verified_email()
        email = self.user.email
        response = self.client.post(self.email_change_code, email, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_with_token_credentials_can_request_for_email_change_code(self):
        self.test_get_authenticated_user_token_credentials()
        email = self.user.email
        response = self.token_client.post(self.email_change_code, {"email": email}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_user_cannot_change_email_with_incorrect_code(self):
        self.test_get_authenticated_user_token_credentials()
        new_email = self.fake.email()
        response = self.token_client.post(self.change_email, {"code": 1234, "email": new_email}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_user_can_change_email_with_correct_code(self):
        self.test_get_authenticated_user_token_credentials()
        new_email = self.fake.email()
        user = self.login_response
        generated_code = Otp.objects.create(user=user, code=self.code, expiry_date=self.expiry_date)
        response = self.token_client.post(self.change_email, {"code": generated_code.code, "email": new_email},
                                          format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_request_for_password_change_code(self):
        response = self.client.post(self.password_change_code, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_without_token_credentials_cannot_request_for_password_change_code(self):
        self.test_user_can_login_with_verified_email()
        email = self.user.email
        response = self.client.post(self.password_change_code, email, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_with_token_credentials_can_request_for_password_change_code(self):
        self.test_get_authenticated_user_token_credentials()
        email = self.user.email
        response = self.token_client.post(self.password_change_code, {"email": email}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_user_cannot_change_password_with_incorrect_code(self):
        self.test_get_authenticated_user_token_credentials()
        new_password = random.randint(100000, 999999)
        response = self.token_client.post(self.change_email, {"code": 1234, "password": new_password}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_user_can_change_password_with_correct_code(self):
        self.test_get_authenticated_user_token_credentials()
        new_password = random.randint(100000, 999999)
        user = self.login_response
        generated_code = Otp.objects.create(user=user, code=self.code, expiry_date=self.expiry_date)
        response = self.token_client.post(self.change_password, {"code": generated_code.code, "password": new_password},
                                          format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_user(self):
        self.test_get_authenticated_user_token_credentials()
        user = self.logout_user_response
        response = self.token_client.post(self.logout, {"refresh": user.data["tokens"]["refresh"]}, user=user,
                                          token=user.data["tokens"]["access"], format="json")
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
