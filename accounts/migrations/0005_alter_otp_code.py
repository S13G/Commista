# Generated by Django 4.1.7 on 2023-03-13 08:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_alter_user_email_alter_user_full_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="code",
            field=models.CharField(max_length=4),
        ),
    ]
