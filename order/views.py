from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa  # pip install xhtml2pdf
from .models import Order  # update this import if your model name differs

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

    context = {
        'orders': orders,
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

    total_amount = sum(item.price * item.quantity for item in items)

    context = {
        'order': order,
        'items': items,
        'total_amount': total_amount,
    }
    return render(request, 'order/order_detail.html', context)

