# Generated by Django 4.1.7 on 2023-05-20 21:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_remove_user_tokens_token_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="token",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tokens",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]