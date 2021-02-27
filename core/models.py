import pytz

from django.db import models
from django.utils import timezone


# Create your models here.
class Vtuber(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    twitter = models.CharField(max_length=20)
    bili_id = models.CharField(max_length=100)


class Live(models.Model):
    dt = models.DateTimeField(default=timezone.localtime(
        timezone=pytz.timezone('Asia/Tokyo')))
    platform = models.TextField()
    vtbs = models.TextField()
