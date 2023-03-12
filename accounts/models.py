from accounts.choices import GENDER_CHOICES
from accounts.validators import validate_phone_number, validate_full_name
from common.models import BaseModel
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4

from .managers import CustomUserManager


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False, unique=True)
    username = None
    full_name = models.CharField(
            _("Full name"), max_length=255, validators=[validate_full_name]
    )
    email = models.EmailField(_("Email address"), unique=True)
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
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.full_name

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }


class Otp(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.user.full_name} ----- {self.code}"
