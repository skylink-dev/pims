from django.contrib import admin
from .models import CustomerAssetMapping

@admin.register(CustomerAssetMapping)
class CustomerAssetMappingAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "phone", "order_serial", "assigned_by", "assigned_at")
    search_fields = ("customer_name", "phone", "order_serial__serial_number")
