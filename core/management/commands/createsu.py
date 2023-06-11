from decouple import config
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates a superuser.'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                    email=config('ADMIN_EMAIL'),
                    password=config('ADMIN_PASSWORD')
            )
        print('Superuser has been created.')
