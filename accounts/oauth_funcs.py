from decouple import config
from django.contrib.auth import authenticate, get_user_model
from faker import Faker
from rest_framework.exceptions import AuthenticationFailed

fake = Faker()

User = get_user_model()


def generate_full_name(name):
    full_name = fake.name().lower()
    while User.objects.filter(full_name=full_name).exists():
        full_name = fake.name().lower()
    return full_name


def register_social_user(provider, user_id, email, name):
    filtered_user_by_email = User.objects.filter(email=email)

    if filtered_user_by_email.exists():
        if provider == filtered_user_by_email[0].auth_provider:
            registered_user = authenticate(email=email, password=config('SOCIAL_SECRET'))
            return {
                "full_name": registered_user.full_name,
                "email": registered_user.email,
                "tokens": registered_user.tokens()
            }
        else:
            raise AuthenticationFailed(f"Please continue your login using {filtered_user_by_email[0].auth_provider}")
    else:
        user = {
            "full_name": generate_full_name(name),
            "email": email,
            "password": config('SOCIAL_SECRET')
        }
        user = User.objects.create_user(**user)
        user.is_verified = True
        user.save()

        new_user = authenticate(email=email, password=config('SOCIAL_SECRET'))
        return {
            'email': new_user.email,
            'full_name': new_user.full_name,
            'tokens': new_user.tokens()
        }
