from django.db import models
from accounts.models import CustomUser

class Partner(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, default='John')
    last_name = models.CharField(max_length=50, default='Doe')
    code = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username
