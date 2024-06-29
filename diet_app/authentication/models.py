# authentication/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    weight = models.FloatField()
    height = models.FloatField()
    dietary_preferences = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    health_goals = models.TextField(blank=True, null=True)
    activity= models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username
