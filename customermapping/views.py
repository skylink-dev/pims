# customermapping/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from partner.models import Partner, PartnerAssetLimit
from .utils import get_customer_by_phone
from order.models import OrderItemSerial,Order,OrderItem
from asset.models import Cart, CartItem
from django.db.models import Sum, F, Q
from asset.models import Asset
from .models import CustomerAssetMapping
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import CustomerAssetMapping

from django.db.models import Max




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
    # Get only this user's orders
    user_orders = Order.objects.filter(user=request.user)
    partner = Partner.objects.get(user=request.user)
    # Related records (filtered through the user's orders)
    order_items = OrderItem.objects.filter(order__in=user_orders)

    cart = Cart.objects.filter(user=request.user).first()
    cart_count = 0
    if cart:
        cart_count = cart_items = CartItem.objects.filter(cart=cart).count()

    serials = (
        OrderItemSerial.objects
        .filter(order_item__order__in=user_orders)
        .annotate(
            mapped_date=Max('customerassetmapping__assigned_at')
        )
        .order_by('-mapped_date')
    )

    total_orders = user_orders.count()
    total_assets = serials.count()
    total_mapped = CustomerAssetMapping.objects.filter(
        order_serial__order_item__order__user=request.user
    ).count()
    total_unmapped = max(total_assets - total_mapped, 0)

    available_assets = []
    for asset in Asset.objects.all():
        serial_count = serials.filter(order_item__asset=asset).count()
        partner_asset_limit = PartnerAssetLimit.objects.filter(partner=partner, asset=asset).first()
       # skip assets without serials
        total_mapped_based_asset = CustomerAssetMapping.objects.filter(
            order_serial__order_item__asset=asset
        ).count()
        ordered_qty = serials.filter(order_item__asset=asset).count()-total_mapped_based_asset

        max_allowed = asset.max_order_per_partner or 0
        remaining_qty = max(max_allowed - ordered_qty-total_mapped_based_asset, 0)
        if partner_asset_limit:
            # If partner-specific limit is defined and lower, use it
            max_allowed = max(max_allowed, partner_asset_limit.max_purchase_limit)
            remaining_qty = max(max_allowed - ordered_qty - total_mapped_based_asset, 0)

        available_assets.append({
            "id": asset.id,
            "name": asset.name,
            "asset_code": asset.asset_code,
            "image": asset.image.url if asset.image else None,
            "max_allowed": max_allowed,
            "ordered_qty": ordered_qty,
            "remaining_qty": remaining_qty,
            "mapped_asset":total_mapped_based_asset,
            "total_assets_bought": serial_count,
        })

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
        "total_orders": total_orders,
        "total_assets": total_assets,
        "total_assets_in_hand": total_assets-total_mapped,
        "total_mapped": total_mapped,
        "total_unmapped": total_unmapped,
        "available_assets":available_assets,
        "cart_count":cart_count
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
