import csv
from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from partner.models import Partner, PartnerCategory


class Command(BaseCommand):
    help = "Import partner data and create or update users with default password."

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        default_password = "Patner@12345"

        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                firm_name = row['FIRM NAME'].strip()
                sd_amount = int(row['SD AMOUNT'].strip())
                partner_name = row['PARTNER NAME'].strip()
                address = row['INVENTORY SHIPPING ADDRESS'].strip()
                phone = row.get('MOBILE', '').strip()

                # Split name
                parts = partner_name.split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''

                # Determine category
                if sd_amount >= 50000:
                    cat_id = 1
                elif sd_amount >= 25000:
                    cat_id = 3
                else:
                    cat_id = 2

                partner_category = PartnerCategory.objects.filter(id=cat_id).first()

                # Username (no spaces, lowercase)
                username = firm_name.replace(' ', '').lower()

                # Create or get user
                user, created = CustomUser.objects.get_or_create(
                    username=username,
                    defaults={
                        'user_type': 'partner',
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': f"{username}@example.com",
                    }
                )

                if created:
                    user.set_password(default_password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"👤 New user created: {username}"))
                else:
                    # Update name fields if missing
                    if not user.first_name:
                        user.first_name = first_name
                    if not user.last_name:
                        user.last_name = last_name
                    user.save()
                    self.stdout.write(self.style.WARNING(f"⚙️ User '{username}' already exists — updating partner info..."))

                # Check for existing partner entry
                partner = Partner.objects.filter(user=user).first()

                if partner:
                    # Update existing partner info
                    partner.first_name = first_name
                    partner.last_name = last_name
                    partner.address = address
                    if phone:  # Only update if phone provided
                        partner.phone = phone
                    partner.partner_category = partner_category
                    partner.refundable_wallet = sd_amount
                    partner.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Partner updated: {firm_name} ({username})"))
                else:
                    # Create new partner
                    next_code = f"skyplay_{1000 + Partner.objects.count()}"
                    Partner.objects.create(
                        user=user,
                        first_name=first_name,
                        last_name=last_name,
                        address=address,
                        phone=phone,
                        partner_category=partner_category,
                        refundable_wallet=sd_amount,
                        code=next_code,
                    )
                    self.stdout.write(self.style.SUCCESS(f"✅ Partner created: {firm_name} ({username})"))
