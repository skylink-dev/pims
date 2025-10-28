from django.db import models
from django.conf import settings  # ✅ Import this
from asset.models import Asset


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # ✅ Fix here
    order_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    dc_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Auto-generated Delivery Challan Number"
    )

    def save(self, *args, **kwargs):
        # Auto-generate DC number if not already set
        if not self.dc_number:
            last_dc = Order.objects.filter(dc_number__isnull=False).order_by('-id').first()
            if last_dc and last_dc.dc_number.startswith('DC'):
                try:
                    last_number = int(last_dc.dc_number.replace('DC', ''))
                except ValueError:
                    last_number = 0
            else:
                last_number = 0
            new_number = last_number + 1
            self.dc_number = f"DC{new_number:04d}"  # DC0001, DC0002, etc.

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id} - {self.user.username}"

    def total_items(self):
        return self.orderitem_set.count()

    def total_amount(self):
        return sum(item.price * item.quantity for item in self.orderitem_set.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    serial_number = models.CharField(max_length=100, blank=True, null=True, help_text="Enter serial number for this item")
    def __str__(self):
        return f"{self.asset.name} x {self.quantity}"

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"


class OrderItemSerial(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='serials')
    serial_number = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_item.asset.name} - {self.serial_number}"