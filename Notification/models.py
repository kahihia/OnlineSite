from django.db import models
import django.utils.timezone
from interpay.models import UserProfile


class Notification(models.Model):
    text = models.CharField(max_length=100)
    time = models.TimeField(default=django.utils.timezone.now)
    user = models.ForeignKey(UserProfile)
    url = models.URLField(max_length=50)
    seen = models.BooleanField(default=0)
