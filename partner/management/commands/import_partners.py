import csv
from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from partner.models import Partner, PartnerCategory


class Command(BaseCommand):
    help = "Import partner data with email & phone update. Creates or updates both User and Partner."

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        default_password = "Partner@12345"

        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                firm_name = row['FIRM NAME'].strip()
                sd_amount = int(row['SD AMOUNT'].strip())
                partner_name = row['PARTNER NAME'].strip()
                address = row['INVENTORY SHIPPING ADDRESS'].strip()

                phone = row.get('MOBILE', '').strip()
                email = row.get('EMAIL', '').strip()

                # --- Name split ---
                parts = partner_name.split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''

                # --- Category Calculation ---
                if sd_amount >= 50000:
                    cat_id = 1
                elif sd_amount >= 25000:
                    cat_id = 3
                else:
                    cat_id = 2

                partner_category = PartnerCategory.objects.filter(id=cat_id).first()

                # --- Username ---
                username = firm_name.replace(' ', '').lower()

                # --- USER CREATE/UPDATE ---
                user, created = CustomUser.objects.get_or_create(
                    username=username,
                    defaults={
                        'user_type': 'partner',
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email if email else f"{username}@example.com",
                    }
                )

                if created:
                    user.set_password(default_password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"👤 User created: {username}"))
                else:
                    # Update missing fields
                    updated = False

                    if first_name and user.first_name != first_name:
                        user.first_name = first_name
                        updated = True

                    if last_name and user.last_name != last_name:
                        user.last_name = last_name
                        updated = True

                    if email and user.email != email:
                        user.email = email
                        updated = True

                    if updated:
                        user.save()
                        self.stdout.write(self.style.WARNING(f"⚙️ Updated user fields for: {username}"))

                # --- PARTNER UPDATE/CREATE ---
                partner = Partner.objects.filter(user=user).first()

                if partner:
                    # Update partner data
                    partner.first_name = first_name
                    partner.last_name = last_name
                    partner.address = address
                    partner.partner_category = partner_category
                    partner.refundable_wallet = sd_amount

                    if phone:
                        partner.phone = phone
                    if email:
                        partner.email = email  # if your model has email

                    partner.save()
                    self.stdout.write(self.style.SUCCESS(f"🔄 Updated Partner: {firm_name}"))
                else:
                    # Create unique code
                    next_code = f"skyplay_{1000 + Partner.objects.count()}"

                    Partner.objects.create(
                        user=user,
                        first_name=first_name,
                        last_name=last_name,
                        address=address,
                        phone=phone,
                        email=email if email else "",  # only if email exists in model
                        partner_category=partner_category,
                        refundable_wallet=sd_amount,
                        code=next_code,
                    )

                    self.stdout.write(self.style.SUCCESS(f"🎉 Partner created: {firm_name}"))
