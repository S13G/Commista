# Generated by Django 4.1.7 on 2023-05-19 10:46

import core.models
import core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_alter_otp_user_alter_profile_gender"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="code",
            field=models.PositiveIntegerField(help_text="The OTP code.", null=True),
        ),
        migrations.AlterField(
            model_name="otp",
            name="expired",
            field=models.BooleanField(
                default=False, help_text="Indicates whether the OTP has expired."
            ),
        ),
        migrations.AlterField(
            model_name="otp",
            name="expiry_date",
            field=models.DateTimeField(
                auto_now_add=True,
                help_text="The date and time when the OTP will expire.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="otp",
            name="user",
            field=models.ForeignKey(
                help_text="The user associated with this OTP.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="otp",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="_avatar",
            field=models.ImageField(
                help_text="The avatar image of the user.",
                upload_to=core.models.upload_path,
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="birthday",
            field=models.DateField(help_text="The birthday of the user.", null=True),
        ),
        migrations.AlterField(
            model_name="profile",
            name="gender",
            field=models.CharField(
                choices=[("M", "Male"), ("F", "Female"), ("O", "Others")],
                help_text="The gender of the user.",
                max_length=1,
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="phone_number",
            field=models.CharField(
                help_text="The phone number of the user.",
                max_length=20,
                validators=[core.validators.validate_phone_number],
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="user",
            field=models.OneToOneField(
                help_text="The user associated with this profile.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                help_text="The email address of the user.", max_length=254, unique=True
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="email_changed",
            field=models.BooleanField(
                default=False,
                help_text="Indicates whether the user has changed their email.",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="is_verified",
            field=models.BooleanField(
                default=False,
                help_text="Indicates whether the user's email is verified.",
            ),
        ),
    ]