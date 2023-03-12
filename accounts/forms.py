from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from accounts.models import User


# ADMIN ACCOUNT CREATION
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "full_name")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email", "full_name")
