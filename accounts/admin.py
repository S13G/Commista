from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.forms import CustomUserChangeForm, CustomUserCreationForm
from accounts.models import Otp, User


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
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


@admin.register(Otp)
class OtpAdmin(admin.ModelAdmin):
    list_display = ["user", "user_email", "code"]

    @admin.display(description='User Email')
    def user_email(self, obj):
        return obj.user.email


admin.site.register(User, CustomUserAdmin)
