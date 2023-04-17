import random
import threading
import warnings

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from core.models import Otp, User


def send_otp_email(user, subject, template_name, code_expiry_time):
    try:
        user = User.objects.get(id=user.id)
    except User.DoesNotExist:
        warnings.warn(f"User with this id {user.id} does not exist")
        return
    code = random.randint(1000, 9999)
    otp = Otp.objects.create(user=user, code=code,
                             expiry_date=timezone.now() + timezone.timedelta(minutes=code_expiry_time))
    context = {'full_name': user.full_name, 'code': otp.code}
    message = render_to_string(template_name, context)
    send_email(subject, message, user.email)


def send_email(subject, message, to):
    msg = EmailMessage(subject=subject, body=message, from_email=settings.EMAIL_HOST_USER, to=[to])
    msg.content_subtype = 'html'
    msg.send()


class Util:
    @staticmethod
    def email_activation(user):
        t = threading.Thread(target=send_otp_email, args=(user, 'Activate Your Account', 'activation_email.html', 15))
        t.start()

    @staticmethod
    def email_change(user):
        t = threading.Thread(target=send_otp_email, args=(user, 'Change Your Email', 'email_change.html', 10))
        t.start()

    @staticmethod
    def email_verified(user):
        context = {'full_name': user.full_name}
        message = render_to_string("verification_email.html", context)
        send_email('Account Verified', message, user.email)

    @staticmethod
    def password_activation(user):
        t = threading.Thread(target=send_otp_email, args=(user, 'Change Your Password', 'password_reset.html', 10))
        t.start()