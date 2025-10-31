# customermapping/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .utils import get_customer_by_phone
from order.models import OrderItemSerial
from .models import CustomerAssetMapping
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import CustomerAssetMapping




@login_required
def get_customer_ajax(request):
    phone = request.GET.get("phone")
    if not phone:
        return JsonResponse({"error": "Phone number required"}, status=400)

    users = get_customer_by_phone(phone)
    if not users:
        return JsonResponse({"error": "No customers found"}, status=404)

    return JsonResponse({"customers": users})

from django.utils.timezone import localtime
@login_required
def customer_asset_mapping(request):
    serials = OrderItemSerial.objects.all().select_related('order_item__order', 'order_item__asset')

    if request.method == "POST" and "assign" in request.POST:
        serial_id = request.POST.get("serial_id")
        phone = request.POST.get("phone")
        name = request.POST.get("name")
        email = request.POST.get("email")
        address = request.POST.get("address")

        if not serial_id:
            return JsonResponse({"error": "Serial ID missing"}, status=400)

        serial = OrderItemSerial.objects.get(id=serial_id)
        order = getattr(serial.order_item, "order", None)

        mapping = CustomerAssetMapping.objects.create(
            customer_name=name,
            phone=phone,
            email=email,
            address=address,
            order_serial=serial,
            assigned_by=request.user
        )

        # ✅ Extract order details
        order_id = getattr(order, "order_id", "N/A") if order else "N/A"
        payment_status = getattr(order, "status", "N/A") if order else "N/A"
        asset_name = getattr(serial.order_item.asset, "name", "N/A")
        mapped_date = mapping.created_at.strftime("%d-%m-%Y %H:%M")

        return JsonResponse({
            "success": True,
            "message": "Mapping successful.",
            "mapping": {
                "customer_name": mapping.customer_name,
                "phone": mapping.phone,
                "order_id": order_id,
                "payment_status": payment_status,
                "asset_name": asset_name,
                "mapped_date": mapped_date,
            }
        })

    return render(request, "customermapping/customer_asset_mapping.html", {
        "serials": serials,
    })





@csrf_exempt
@require_POST
def assign_customer(request):
    """
    Assign a customer to a specific order serial and store Sky ID (username from API).
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        serial_id = data.get("serial_id")
        name = data.get("name")
        phone = data.get("phone")
        email = data.get("email", "")
        address = data.get("address", "")
        skyid = data.get("username", "")  # ✅ coming from API response
        print(skyid, "skyid")
        # Validate input
        if not all([serial_id, name, phone]):
            return JsonResponse({"error": "Missing required fields."}, status=400)

        # Get the serial
        try:
            order_serial = OrderItemSerial.objects.get(id=serial_id)
        except OrderItemSerial.DoesNotExist:
            return JsonResponse({"error": "Serial not found."}, status=404)

        # Check if already mapped
        if CustomerAssetMapping.objects.filter(order_serial=order_serial).exists():
            return JsonResponse({"error": "This serial is already mapped."}, status=400)

        asset = order_serial.order_item.asset  # ✅ Get asset object
  # ✅ Prevent same serial from being assigned to the same customer again
        if CustomerAssetMapping.objects.filter(phone=phone, order_serial__order_item__asset=asset).exists():
             return JsonResponse({
                "error": "This customer already has an assigned asset. One user can have only one asset."
            }, status=400)
        # Create new mapping
        mapping = CustomerAssetMapping.objects.create(
            order_serial=order_serial,
            customer_name=name,
            phone=phone,
            email=email,
            address=address,
            skyid=skyid,  # ✅ store Sky ID here
        )

        return JsonResponse({
            "success": True,
            "message": "Mapping successful.",
            "mapping": {
                "id": mapping.id,
                "serial": order_serial.serial_number,
                "customer_name": mapping.customer_name,
                "phone": mapping.phone,
                "skyid": mapping.skyid,  # ✅ return Sky ID in response
            },
        })

    except Exception as e:
        print("Error assigning customer:", e)
        return JsonResponse({"error": str(e)}, status=500)
