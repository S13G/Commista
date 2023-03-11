from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.forms import UserCreationForm, UserChangeForm
from accounts.models import User


class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = (
        "email",
        "full_name",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "email",
        "full_name",
        "is_staff",
        "is_active",
    )
    fieldsets = (
        ("Personal Information", {"fields": ("email", "full_name", "password")}),
        (
            "Permissions",
            {"fields": ("is_staff", "is_active", "groups", "user_permissions")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)


admin.site.register(User, CustomUserAdmin)
