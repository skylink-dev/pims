import csv
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings
from accounts.models import CustomUser


class Command(BaseCommand):
    help = "Send login emails to ZM users from CSV with CC"

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file', type=str, help='Path to the CSV file containing ZM user details'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        # CC recipients
        cc_list = ['rajeswaran@skyplay.in', 'dir-tech@skylink.net.in', 'developer@skylink.net.in']

        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                name = row.get('Name', '').strip()
                username = row.get('User Id', '').strip()
                password = row.get('Password', '').strip()
                email = row.get('Official Email ID', '').strip()
                mobile = row.get('Mobile Number', '').strip()
                designation = row.get('Designation', '').strip()

                if not email:
                    self.stdout.write(self.style.WARNING(f"⚠️ No email for {name}, skipping"))
                    continue

                subject = "Login Details for SIMS Partner & Admin"
                body = f"""
Hi {name},

I hope this message finds you well.

Please find below your login details for the SIMS Partner Application and Admin Panel:

SIMS Partner Application:
URL: https://partner.skyplay.app
Username: {username}
Password: {password}

Admin Panel:
URL: https://admin.skyplay.app/admin
Username: {username}
Password: {password}

You can also reach us at:
Email: info@skylink.net.in
Phone: (+91) 99441 99445

Note: This access is valid for one week only. For any clarifications or issues, please feel free to reach out to us.

Best regards,
Skyplay Team
"""

                # Send email with CC
                try:
                    email_message = EmailMessage(
                        subject=subject,
                        body=body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[email],
                        cc=cc_list
                    )
                    email_message.send(fail_silently=False)
                    self.stdout.write(self.style.SUCCESS(f"✅ Email sent to {name} ({email})"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Failed to send email to {name}: {e}"))
