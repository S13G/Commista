# Generated by Django 4.1.7 on 2023-03-13 16:16

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0009_user_auth_token"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="auth_token",
        ),
    ]
