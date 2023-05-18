from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def handle_profile_creation(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_delete, sender=Profile)
def handle_user_account_deletion(sender, instance, **kwargs):
    try:
        user = getattr(instance, 'user')
        user.delete()
    except User.DoesNotExist:
        pass
