from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from accounts.choices import GENDER_CHOICES
from accounts.validators import validate_full_name, validate_phone_number
from common.models import BaseModel
from .managers import CustomUserManager


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False, unique=True)
    username = None
    full_name = models.CharField(max_length=255, validators=[validate_full_name])
    email = models.EmailField(unique=True)
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1)
    birthday = models.DateField(null=True)
    phone_number = models.CharField(max_length=20, validators=[validate_phone_number])
    avatar = models.ImageField(upload_to="avatar/images")
    email_changed = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.full_name


class Otp(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp")
    code = models.PositiveIntegerField(null=True)
    expired = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.user.full_name} ----- {self.code}"

    def save(self, *args, **kwargs):
        self.expired = self.expiry_date >= timezone.now() + timezone.timedelta(minutes=20)
        super(Otp, self).save(*args, **kwargs)
