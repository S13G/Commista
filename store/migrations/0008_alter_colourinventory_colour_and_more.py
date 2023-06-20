# Generated by Django 4.1.9 on 2023-06-16 16:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0007_alter_colourinventory_colour_and_more"),
    ]

    operations = [
        migrations.AlterField(
                model_name="colourinventory",
                name="colour",
                field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_color",
                        to="store.colour",
                ),
        ),
        migrations.AlterField(
                model_name="colourinventory",
                name="product",
                field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="color_inventory",
                        to="store.product",
                ),
        ),
        migrations.AlterField(
                model_name="sizeinventory",
                name="product",
                field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="size_inventory",
                        to="store.product",
                ),
        ),
        migrations.AlterField(
                model_name="sizeinventory",
                name="size",
                field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_size",
                        to="store.size",
                ),
        ),
    ]