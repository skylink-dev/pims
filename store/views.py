from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from order.models import Order, OrderItem, OrderItemSerial

def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'store/order_list.html', {'orders': orders})

def update_serials(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    if request.method == 'POST':
        serials = request.POST.getlist('serial_numbers')

        # Clear old serials
        item.serials.all().delete()

        # Add new serials
        for s in serials:
            if s.strip():
                OrderItemSerial.objects.create(order_item=item, serial_number=s.strip())

        # If all item serials match quantities, update order status
        if all(i.serials.count() >= i.quantity for i in item.order.orderitem_set.all()):
            item.order.status = 'Serial Updated'
            item.order.save()

        messages.success(request, f"Serial numbers updated for {item.asset.name}")
        return redirect('order_list')

    return redirect('order_list')

def mark_order_completed(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = "Completed"
    order.save()
    messages.success(request, f"✅ Order {order.order_id} marked as completed successfully!")
    return redirect('order_list')