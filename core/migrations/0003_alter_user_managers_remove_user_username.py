# Generated by Django 4.1.7 on 2023-05-18 11:34

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_alter_user_managers_user_username"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[],
        ),
        migrations.RemoveField(
            model_name="user",
            name="username",
        ),
    ]