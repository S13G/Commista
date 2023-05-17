from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from common.models import BaseModel
from core.choices import GENDER_CHOICES
from core.validators import validate_phone_number
from .managers import CustomUserManager


def upload_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/customer/instance_id/<filename>
    return f"customer/{instance.id[:5]}/{filename}"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False, unique=True)
    username = None
    email = models.EmailField(unique=True)
    email_changed = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    @property
    def full_name(self):
        return self.get_full_name()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1)
    birthday = models.DateField(null=True)
    phone_number = models.CharField(max_length=20, validators=[validate_phone_number])
    _avatar = models.ImageField(upload_to=upload_path)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return self.user.full_name

    @property
    def avatar(self):
        if self._avatar is not None:
            return self._avatar.url
        return None


class Otp(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_codes")
    code = models.PositiveIntegerField(null=True)
    expired = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(null=True, auto_now_add=True, editable=False)

    def __str__(self):
        return f"{self.user.full_name} ----- {self.code}"

    def save(self, *args, **kwargs):
        self.expiry_date += timezone.timedelta(minutes=15)
        if timezone.now() == self.expiry_date:
            self.expired = True
            self.delete()
        super(Otp, self).save(*args, **kwargs)
