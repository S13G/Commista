from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_phone_number(value):
    if not value.startswith('+'):
        raise ValidationError(_("Phone number must start with a plus sign (+)"))
    if not value[1:].isdigits():
        raise ValidationError(_("Phone number must only contain digits after the plus sign (+)"))
    
def validate_full_name(value):
    words = value.strip().split()
    if len(words) != 2:
        raise ValidationError(_("Full name must consist of two words"))