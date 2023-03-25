from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.forms import CustomUserChangeForm, CustomUserCreationForm
from core.models import User


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = (
        "email",
        "full_name",
        "is_staff",
        "is_active",
        "is_verified",
        "email_changed",
    )
    list_filter = (
        "email",
        "full_name",
        "is_staff",
        "is_active",
    )
    fieldsets = (
        ("Personal Information", {"fields": (
            "email", "full_name", "password", "gender", "birthday", "avatar", "email_changed", "is_verified")}),
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
