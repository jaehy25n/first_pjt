from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    pass

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reading_goal = models.CharField(max_length=200, blank=True)
    # primary_library = models.ForeignKey('recommend.Library', on_delete=models.SET_NULL, null=True, blank=True) # 나중에 연결

    def __str__(self):
        return f"{self.user.username}'s Profile"
