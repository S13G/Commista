from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from accounts.models import User


# ADMIN ACCOUNT CREATION
class UserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",)


class UserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email",)
