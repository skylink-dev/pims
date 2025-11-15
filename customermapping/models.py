from django.conf import settings  # ✅ import this instead of User
from order.models import OrderItemSerial
from django.db import models

class CustomerAssetMapping(models.Model):
    customer_name = models.CharField(max_length=255, default="Unknown")
    phone = models.CharField(max_length=15, default="0000000000")
    email = models.EmailField(blank=True, null=True, default="")
    address = models.TextField(blank=True, null=True, default="")
    order_serial = models.ForeignKey(OrderItemSerial, on_delete=models.CASCADE, null=True, blank=True)
    assigned_by = models.ForeignKey(  # ✅ updated field
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    skyid = models.CharField(max_length=100, blank=True, null=True)  

    class Meta:
        verbose_name = "Customer Device Mapping"
        verbose_name_plural = "Customer Device Mappings"
        
    def __str__(self):
        return f"{self.customer_name} ({self.phone}) - {self.order_serial}"
