from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

# ✅ Import from order app (correct app)
from order.models import Order, OrderItem, OrderItemSerial, OrderShipment


# 🧾 Store Orders List
def store_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'store/order_list.html', {'orders': orders})


# 🔢 Update Serial Numbers
def update_serials(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)

    if request.method == 'POST':
        serials = request.POST.getlist('serial_numbers')
        makes = request.POST.getlist('make')
        models_ = request.POST.getlist('model')
        mac_ids = request.POST.getlist('mac_id')

        # Clear old serials
        item.serials.all().delete()

        # Add new serials with optional fields
        for s, mk, mdl, mac in zip(serials, makes, models_, mac_ids):
            if s.strip():
                OrderItemSerial.objects.create(
                    order_item=item,
                    serial_number=s.strip(),
                    make=mk.strip() or None,
                    model=mdl.strip() or None,
                    mac_id=mac.strip() or None
                )

        # ✅ Optional: Update status
        if all(i.serials.count() >= i.quantity for i in item.order.orderitem_set.all()):
            item.order.status = 'Serial Updated'
            item.order.save()

        messages.success(request, f"Serial numbers updated for {item.asset.name}")
        return redirect('store_orders')

    return redirect('store_orders')

# ✅ Mark Order Completed
def mark_order_completed(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = "Completed"
    order.save()
    messages.success(request, f"✅ Order {order.order_id} marked as completed successfully!")
    return redirect('store_orders')


# 📦 Store Order Detail Page
def store_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.orderitem_set.all()
    shipment = getattr(order, 'shipment', None)  # ✅ safer way (OneToOne)
    total_amount = sum(item.price * item.quantity for item in items)

    return render(request, 'store/order_detail.html', {
        'order': order,
        'items': items,
        'shipment': shipment,
           'total_amount': total_amount
    })


# 🚚 Add Shipment Details
def add_shipment(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # ✅ Allow only if shipment doesn’t exist yet
    if hasattr(order, 'shipment'):
        messages.warning(request, "Shipment details already exist for this order.")
        return redirect('store_order_detail', order_id=order_id)

    if request.method == "POST":
        courier_name = request.POST.get("courier_name")
        tracking_id = request.POST.get("tracking_id")
        remarks = request.POST.get("remarks")

        OrderShipment.objects.create(
            order=order,
            courier_name=courier_name,
            tracking_id=tracking_id,
            remarks=remarks,
            dispatched_at=timezone.now(),
            shipping_status=1,  # In Transit
        )

        messages.success(request, "✅ Shipment details added successfully.")
        return redirect('store_order_detail', order_id=order_id)

    return render(request, 'store/add_shipment.html', {'order': order})



def edit_shipment(request, order_id):
    shipment = get_object_or_404(OrderShipment, order__id=order_id)

    if request.method == "POST":
        courier_name = request.POST.get("courier_name")
        tracking_id = request.POST.get("tracking_id")
        dispatched_at = request.POST.get("dispatched_at")
        delivered_at = request.POST.get("delivered_at")
        remarks = request.POST.get("remarks")
        shipping_status = request.POST.get("shipping_status")

        # ✅ Update fields
        shipment.courier_name = courier_name
        shipment.tracking_id = tracking_id
        shipment.remarks = remarks
        shipment.shipping_status = int(shipping_status) if shipping_status else 0

        # ✅ Parse datetime safely
        def parse_dt(dt):
            try:
                return timezone.make_aware(timezone.datetime.strptime(dt, "%Y-%m-%dT%H:%M"))
            except Exception:
                return None

        if dispatched_at:
            shipment.dispatched_at = parse_dt(dispatched_at)
        if delivered_at:
            shipment.delivered_at = parse_dt(delivered_at)

        shipment.save()
        messages.success(request, "✅ Shipment details updated successfully!")
        return redirect("store_order_detail", order_id=order_id)  
    return render(request, "store/edit_shipment.html", {"shipment": shipment})