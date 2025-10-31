from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa  # pip install xhtml2pdf

from asset.models import CartItem,Cart
from .models import Order  # update this import if your model name differs
import json
import base64
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def order_summary_pdf(request, order_id):
    order = Order.objects.get(id=order_id)
    template_path = 'order/delivery_challan.html'  # path to your HTML template
    context = {'order': order, 'partner': order.partner}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="DeliveryChallan_{order.id}.pdf"'
    
    # Render HTML to PDF
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors while generating PDF <pre>' + html + '</pre>')
    return response


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem

@login_required
def orders_list(request):
    """
    Display all orders for the logged-in user.
    """
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')
    cart = Cart.objects.filter(user=request.user).first()
    cart_count = 0

    if cart:
        cart_count = cart_items = CartItem.objects.filter(cart=cart).count()

    context = {
        'orders': orders,
        "cart_count":cart_count

    }
    return render(request, 'order/orders_list.html', context)


@login_required
def order_detail(request, pk):
    """
    Display a detailed summary of a specific order.
    """
    user = request.user
    order = get_object_or_404(Order, pk=pk, user=user)
    items = OrderItem.objects.filter(order=order)
    shipment = getattr(order, 'shipment', None)
    total_amount = sum(item.price * item.quantity for item in items)
    cart = Cart.objects.filter(user=request.user).first()
    cart_count = 0

    if cart:
        cart_count = cart_items = CartItem.objects.filter(cart=cart).count()

    context = {
        'order': order,
        'items': items,
        'total_amount': total_amount,
        'shipment':shipment,
        'cart_count':cart_count

    }
    return render(request, 'order/order_detail.html', context)


import base64
import json
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os

@csrf_exempt
def mark_order_received(request, order_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order = get_object_or_404(Order, id=order_id)
            shipment = getattr(order, 'shipment', None)

            if not shipment:
                return JsonResponse({"success": False, "message": "No shipment found for this order."})

            # ✅ Handle signature saving
            signature_data = data.get("signature")
            if signature_data:
                format, imgstr = signature_data.split(";base64,")
                ext = format.split("/")[-1]
                filename = f"signature_{order.order_id}.{ext}"
                file_path = os.path.join(settings.MEDIA_ROOT, "signature", filename)

                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(imgstr))

                # Store relative path in DB
                shipment.signature = f"signature/{filename}"

            shipment.shipping_status = 2  # Delivered
            shipment.delivered_at = timezone.now()
            shipment.save()

            # Update order
            order.status = "Completed"
            order.save()

            # ✅ Safe JSON serialization
            signature_url = f"media/{settings.MEDIA_URL}signature/{filename}" if signature_data else None

            return JsonResponse({
                "success": True,
                "message": f"Order #{order.order_id} marked as received!",
                "signature_url": signature_url
            })

        except Order.DoesNotExist:
            return JsonResponse({"success": False, "message": "Order not found."})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request."})