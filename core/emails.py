import random
import threading
import warnings

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from core.models import Otp, User


# This function sends an activation email to a user with an OTP code to change their password.
# It takes a user ID as input and retrieves the user object from the database.
def password_verification_email(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        warnings.warn(f"User with this id {user_id} does not exist")
        return
    code = random.randint(1000, 9999)
    otp = Otp.objects.create(user=user, code=code, expiry_date=timezone.now() + timezone.timedelta(minutes=10))
    context = {'full_name': user.full_name, 'code': otp.code}
    message = render_to_string("password_reset.html", context)
    msg = EmailMessage(subject='Change Your Password', body=message, from_email=settings.EMAIL_HOST_USER,
                       to=[user.email])
    msg.content_subtype = 'html'
    msg.send()


# This function sends an activation email to a user with an OTP code to verify their account.
# It takes a user ID as input and retrieves the user object from the database.
def send_activation_email(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        warnings.warn(f"User with this id {user_id} does not exist")
        return
    code = random.randint(1000, 9999)
    otp = Otp.objects.create(user=user, code=code, expiry_date=timezone.now() + timezone.timedelta(minutes=15))
    context = {'full_name': user.full_name, 'code': otp.code}
    message = render_to_string("activation_email.html", context)
    msg = EmailMessage(subject='Activate Your Account', body=message, from_email=settings.EMAIL_HOST_USER,
                       to=[user.email])
    msg.content_subtype = 'html'
    msg.send()


# This function sends an email change email to a user with an OTP code to change their email.
# It takes a user ID as input and retrieves the user object from the database.
def send_email_change_verification(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        warnings.warn(f"User with this id {user_id} does not exist")
        return
    code = random.randint(1000, 9999)
    otp = Otp.objects.create(user=user, code=code, expiry_date=timezone.now() + timezone.timedelta(minutes=10))
    context = {'full_name': user.full_name, 'code': otp.code}
    message = render_to_string("email_change.html", context)
    msg = EmailMessage(subject='Change Your Email', body=message, from_email=settings.EMAIL_HOST_USER,
                       to=[user.email])
    msg.content_subtype = 'html'
    msg.send()


# This function sends an activation email to a user with an OTP code to verify their account.
# It takes a user ID as input and retrieves the user object from the database.
def send_verification_email(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        warnings.warn(f"User with this id {user_id} does not exist")
        return
    context = {'full_name': user.full_name}
    message = render_to_string("verification_email.html", context)
    msg = EmailMessage(subject='Account Verified', body=message, from_email=settings.EMAIL_HOST_USER,
                       to=[user.email])
    msg.content_subtype = 'html'
    msg.send()


class Util:
    @staticmethod
    def email_activation(user):
        t = threading.Thread(target=send_activation_email, args=(user.id,))
        t.start()

    @staticmethod
    def email_change(user):
        t = threading.Thread(target=send_email_change_verification, args=(user.id,))
        t.start()

    @staticmethod
    def email_verified(user):
        t = threading.Thread(target=send_verification_email, args=(user.id,))
        t.start()

    @staticmethod
    def password_activation(user):
        t = threading.Thread(target=password_verification_email, args=(user.id,))
        t.start()
