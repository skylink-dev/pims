import csv
from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from partner.models import Partner


class Command(BaseCommand):
    help = "Fix existing partner emails and phone numbers using the original CSV input."

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        with open(csv_file, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                firm_name = row['FIRM NAME'].strip()
                email = row.get('EMAIL', '').strip()
                phone = row.get('MOBILE', '').strip()

                # username = firm name without spaces
                username = firm_name.replace(' ', '').lower()

                try:
                    user = CustomUser.objects.get(username=username)
                except CustomUser.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"❌ User not found for: {firm_name}"))
                    continue

                partner = Partner.objects.filter(user=user).first()
                if not partner:
                    self.stdout.write(self.style.ERROR(f"❌ Partner entry missing for: {firm_name}"))
                    continue

                # ------------------------------
                # UPDATE EMAIL
                # ------------------------------
                if email and user.email != email:
                    user.email = email
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"📧 Updated email: {firm_name} → {email}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Email already correct for {firm_name}"))

                # ------------------------------
                # UPDATE PHONE (CustomUser + Partner)
                # ------------------------------
                if phone:
                    updated = False

                    if user.phone != phone:
                        user.phone = phone
                        updated = True
                        user.save()

                    if partner.phone != phone:
                        partner.phone = phone
                        updated = True
                        partner.save()

                    if updated:
                        self.stdout.write(self.style.SUCCESS(f"📞 Updated phone: {firm_name} → {phone}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Phone already correct for {firm_name}"))

                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ No phone found in CSV for {firm_name}"))
