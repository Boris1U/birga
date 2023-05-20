from typing import Iterable, Optional
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from PIL import Image


class Type(models.TextChoices):
    PERSONAL = 'PR', _('Личный')
    BUSINESS = 'BS', _('Бизнес')


class Profile(AbstractUser):
    image = models.ImageField(null=True, blank=True, upload_to='profile_pics')

    garantex_secret_key = models.TextField(null=True, blank=True)
    garanted_uid = models.TextField(null=True, blank=True)
    garantex_jwt = models.TextField(null=True, blank=True)

    binance_secret_key = models.TextField(null=True, blank=True)
    binance_api = models.TextField(null=True, blank=True)

    accounts = models.ManyToManyField('Profile',blank=True)

    type = models.CharField(max_length=2, choices=Type.choices, default=Type.PERSONAL)
    subscription_active = models.BooleanField(verbose_name='Подписка активна?', default=False)
    subscription_expiration_date = models.DateField(verbose_name='Дата истечения подписки', null=True, blank=True)

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)

        if self.image:
            img = Image.open(self.image.path)

            output_size = (260, 260)
            img.thumbnail(output_size)
            img.save(self.image.path)


class News(models.Model):
    site = models.TextField()
    image_link = models.TextField()
    text = models.TextField()
    refresh = models.DateTimeField(auto_now_add=True)
    link = models.TextField(null=True, blank=True)


class History(models.Model):
    account = models.ForeignKey(to=Profile, on_delete=models.CASCADE)
    currency = models.TextField()
    birja = models.TextField()
    created_at = models.DateTimeField()
    side = models.TextField()
    volume = models.FloatField()
    total_price = models.FloatField()


class PayHistory(models.Model):
    account = models.ForeignKey(to=Profile, on_delete=models.DO_NOTHING)
    number = models.BigAutoField(auto_created=True, primary_key=True, editable=False)
    status = models.CharField(max_length=30)
