import random


import requests
from urllib.parse import urlencode
from django.conf import settings


# MSG91 API Configuration
MSG91_API_URL = "https://api.msg91.com/api/sendhttp.php"

AUTH_KEY = "437052AwuTl8Nuu367ea608cP1"
SENDER_ID = "SKYLTD"
TEMPLATE_ID = "1407165460465145131"


def generate_verification_code():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))


