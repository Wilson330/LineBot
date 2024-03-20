# Generated by Django 4.2.10 on 2024-02-29 08:07

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("orderRaiser", models.CharField(max_length=20)),
                ("orderShop", models.CharField(max_length=20)),
                ("orderManu", models.ImageField(upload_to="image/")),
                ("lastModifiedTime", models.DateTimeField(auto_now=True)),
                ("createdTime", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
