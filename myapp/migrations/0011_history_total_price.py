# Generated by Django 4.1.7 on 2023-04-04 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='history',
            name='total_price',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
