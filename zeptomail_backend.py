import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

class ZeptoMailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent_count = 0
        for message in email_messages:
            payload = {
                "from": {"address": settings.ZEPTOMAIL_FROM_EMAIL},
                "to": [{"email_address": {"address": ", ".join(message.to)}}],
                "subject": message.subject,
                "htmlbody": message.body,
            }

            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Zoho-enczapikey {settings.ZEPTOMAIL_API_KEY}",
            }

            response = requests.post(
                settings.ZEPTOMAIL_API_URL,
                json=payload,
                headers=headers,
            )

            if response.status_code == 200:
                sent_count += 1

        return sent_count
