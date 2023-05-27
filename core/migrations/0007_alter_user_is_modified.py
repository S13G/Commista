# Generated by Django 4.1.7 on 2023-05-20 17:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_user_is_modified_alter_user_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="is_modified",
            field=models.DateTimeField(
                default=None,
                editable=False,
                help_text="Indicates the date the user email was changed.",
                null=True,
            ),
        ),
    ]