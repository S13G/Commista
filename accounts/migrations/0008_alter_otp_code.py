# Generated by Django 4.1.7 on 2023-03-13 08:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_alter_otp_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="code",
            field=models.PositiveIntegerField(null=True),
        ),
    ]
