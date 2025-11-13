import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from asset.models import Asset
from order.models import Order, OrderItem, OrderItemSerial
from partner.models import Partner

User = get_user_model()


class Command(BaseCommand):
    help = "Import order data from CSV using existing partners and assets; create if missing"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file}"))
            return

        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                partner_name = row.get('Partner', '').strip()
                if not partner_name:
                    self.stdout.write(self.style.WARNING(f"Partner name missing. Skipping row: {row}"))
                    continue

                username = partner_name.replace(' ', '').lower()

                # Get existing user
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"User {username} not found. Skipping row."))
                    continue

                # Check partner exists
                partner = Partner.objects.filter(user=user).first()
                if not partner:
                    self.stdout.write(self.style.WARNING(f"Partner for user {username} not found. Skipping row."))
                    continue

                # Get or create Asset
                asset_name = row.get('Asset', '').strip()
                if not asset_name:
                    self.stdout.write(self.style.WARNING(f"Asset name missing. Skipping row: {row}"))
                    continue

                asset, created = Asset.objects.get_or_create(
                    name=asset_name,
                    defaults={
                        'location': row.get('Location', '').strip(),
                        'quantity': 1,
                        'asset_code': f"{asset_name[:3].upper()}-{Asset.objects.count()+1:04d}",
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"🆕 Asset '{asset_name}' created"))

                # Update asset location if missing
                location = row.get('Location', '').strip()
                if location and not asset.location:
                    asset.location = location
                    asset.save()

                # Parse dispatched date
                try:
                    order_date = datetime.strptime(row['Dispatched Date'], '%d.%m.%Y')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Invalid date for row {row}: {e}"))
                    order_date = datetime.now()

                # Use Serial Number if available, else fallback to MAC Number
                serial_number = row.get('Serial Number', '').strip() or row.get('MAC Number', '').strip()
                if not serial_number:
                    self.stdout.write(self.style.WARNING(f"No Serial Number or MAC Number for row: {row}. Skipping."))
                    continue

                # Check if order already exists for this user + serial
                order_id = f"OLD-{serial_number}"
                order = Order.objects.filter(order_id=order_id).first()
                if not order:
                    order = Order.objects.create(
                        user=user,
                        order_id=order_id,
                        amount=0.0,
                        status='Completed',  # ✅ Set Completed status
                    )
                    # Override created_at with dispatched date
                    Order.objects.filter(pk=order.pk).update(created_at=order_date)

                    self.stdout.write(self.style.SUCCESS(f"✅ Order created: {order_id} with Completed status"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠ Order {order_id} already exists."))

                # Check if OrderItem exists for this order + asset
                order_item = OrderItem.objects.filter(order=order, asset=asset).first()
                if not order_item:
                    order_item = OrderItem.objects.create(
                        order=order,
                        asset=asset,
                        quantity=1,
                        price=0.0
                    )
                    self.stdout.write(self.style.SUCCESS(f"✅ OrderItem created for {asset.name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠ OrderItem for {asset.name} already exists in this order."))

                # Check if Serial exists globally
                serial = OrderItemSerial.objects.filter(serial_number=serial_number).first()
                if not serial:
                    OrderItemSerial.objects.create(
                        order_item=order_item,
                        serial_number=serial_number,
                        make=asset.name,
                        model=row.get('MAC Number', ''),
                        mac_id=row.get('MAC Number', '')
                    )
                    self.stdout.write(self.style.SUCCESS(f"✅ Serial {serial_number} created"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠ Serial {serial_number} already exists. Skipping."))

        self.stdout.write(self.style.SUCCESS("✅ All orders imported successfully!"))
