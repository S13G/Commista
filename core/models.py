from datetime import timedelta
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from core.choices import GENDER_CHOICES
from core.validators import validate_phone_number
from .managers import CustomUserManager


def upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/customer/instance_id/<filename>
    return f"customer_profile/{filename}"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False, unique=True)
    username = None
    email = models.EmailField(unique=True)
    email_changed = models.BooleanField(
            default=False, help_text=_("Indicates whether the user has changed their email.")
    )
    is_verified = models.BooleanField(
            default=False, help_text=_("Indicates whether the user's email is verified.")
    )
    is_modified = models.DateTimeField(
            default=None, null=True, editable=False, help_text=_("Indicates the date the user email was changed.")
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    @property
    def full_name(self):
        return self.get_full_name()

    def save(self, *args, **kwargs):
        if self.email_changed and not self.is_modified:
            self.is_modified = timezone.now()
        elif self.email_changed and self.is_modified + timedelta(days=10) <= timezone.now():
            self.email_changed = False

        super().save(*args, **kwargs)


class Otp(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp",
                             help_text=_("The user associated with this OTP."))
    code = models.PositiveIntegerField(null=True, help_text=_("The OTP code."))
    expired = models.BooleanField(default=False, help_text=_("Indicates whether the OTP has expired."))
    expiry_date = models.DateTimeField(null=True, editable=False,
                                       help_text=_("The date and time when the OTP will expire."))

    def __str__(self):
        return f"{self.user.full_name} ----- {self.code}"


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile",
                                help_text=_("The user associated with this profile."))
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1, help_text=_("The gender of the user."))
    birthday = models.DateField(null=True, help_text=_("The birthday of the user."))
    phone_number = models.CharField(max_length=20, validators=[validate_phone_number],
                                    help_text=_("The phone number of the user."))
    _avatar = models.ImageField(upload_to=upload_path, help_text=_("The avatar image of the user."))

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

    @property
    def email_address(self):
        return self.user.email
