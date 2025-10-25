from django.db import models
from accounts.models import CustomUser

class Store(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, default='Store')
    last_name = models.CharField(max_length=50, default='Owner')

    def __str__(self):
        return self.user.username
