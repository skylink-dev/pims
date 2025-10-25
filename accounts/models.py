from django.contrib.auth.models import AbstractUser
from django.db import models

USER_TYPE_CHOICES = (
    ('superadmin', 'Super Admin'),
    ('partner', 'Partner'),
    ('store', 'Store'),
)

class CustomUser(AbstractUser):
    username = models.CharField("User ID", max_length=50, unique=True)  # user_id
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='partner')
    code = models.CharField(max_length=20, blank=True, null=True)

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.username} ({self.user_type})"

