from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    pass

class Interest(models.Model):
    name = models.CharField(max_length=100)
    kdc_prefix = models.CharField(max_length=10)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reading_goal = models.CharField(max_length=200, blank=True)
    interests = models.ManyToManyField(Interest, related_name='profiles', blank=True)
    # primary_library = models.ForeignKey('recommend.Library', on_delete=models.SET_NULL, null=True, blank=True) # 나중에 연결

    def __str__(self):
        return f"{self.user.username}'s Profile"
