# Generated by Django 4.1.7 on 2023-04-01 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_profile_subscription_active_profile_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='subscription_expiration_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата истечения подписки'),
        ),
    ]
