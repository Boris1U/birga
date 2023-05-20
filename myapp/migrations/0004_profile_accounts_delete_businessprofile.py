# Generated by Django 4.1.7 on 2023-04-01 10:26

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_profile_binance_jwt_profile_binance_secret_key_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='accounts',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='BusinessProfile',
        ),
    ]
