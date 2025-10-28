from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib import admin
from django.utils.html import format_html
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from .models import Order, OrderItem, OrderItemSerial
from partner.models import Partner


# --------------------------------------------
# COMPANY INFO (Constant)
# --------------------------------------------
COMPANY_INFO = """
<strong>From:</strong><br>
Skylink Fibernet Private Limited,<br>
B6, II Floor, Vue Grande,<br>
339 Chinnaswamy Road, Siddha Pudhur,<br>
Coimbatore - 641044.<br>
info@skylink.net.in<br>
(+91) 99441 99445
"""


# --------------------------------------------
# INLINE ADMIN CLASSES
# --------------------------------------------

class OrderItemSerialInline(admin.TabularInline):
    """Inline for serial numbers — appears under OrderItemAdmin"""
    model = OrderItemSerial
    extra = 0
    fields = ('serial_number', 'created_at')
    readonly_fields = ('created_at',)


class OrderItemInline(admin.TabularInline):
    """Inline for order items — appears under OrderAdmin"""
    model = OrderItem
    extra = 0
    fields = ('asset', 'quantity', 'price', 'subtotal')
    readonly_fields = ('subtotal',)

    def subtotal(self, obj):
        if obj.price and obj.quantity:
            return f"₹{obj.price * obj.quantity:.2f}"
        return "-"
    subtotal.short_description = "Subtotal"


# --------------------------------------------
# MAIN ADMIN: ORDER
# --------------------------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id', 'user', 'status', 'dc_number',
        'amount_display', 'total_items', 'created_at', 'view_summary_link'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('order_id', 'user__username', 'dc_number')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]  # ✅ Only OrderItem here (Serial belongs to OrderItemAdmin)

    readonly_fields = (
        'order_id', 'user', 'amount', 'razorpay_payment_id',
        'razorpay_signature', 'status', 'created_at', 'order_summary'
    )

    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'status', 'created_at', 'dc_number')
        }),
        ('Payment Details', {
            'fields': ('amount', 'razorpay_payment_id', 'razorpay_signature')
        }),
        ('Summary', {
            'fields': ('order_summary',)
        }),
    )

    # ----------------------------
    # FORMATTED AMOUNT DISPLAY
    # ----------------------------
    def amount_display(self, obj):
        return f"₹{obj.amount:.2f}"
    amount_display.short_description = "Amount"

    # ----------------------------
    # LINK TO DELIVERY CHALLAN POPUP
    # ----------------------------
    def view_summary_link(self, obj):
        url = reverse('admin:order_summary_popup', args=[obj.id])
        return mark_safe(f'<a class="button" href="{url}" target="_blank">View DC</a>')
    view_summary_link.short_description = "Delivery Challan"

    # ----------------------------
    # CUSTOM ADMIN URLS
    # ----------------------------
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('summary/<int:order_id>/', self.admin_site.admin_view(self.order_summary_popup),
                 name='order_summary_popup'),
            path('summary/<int:order_id>/pdf/', self.admin_site.admin_view(self.download_dc_pdf),
                 name='order_dc_pdf'),
        ]
        return custom_urls + urls

    # ----------------------------
    # POPUP SUMMARY VIEW (HTML)
    # ----------------------------
    def order_summary_popup(self, request, order_id):
        order = Order.objects.get(pk=order_id)
        partner = getattr(order.user, 'partner', None)
        return HttpResponse(render_to_string('admin/order_summary_popup.html', {
            'order': order,
            'partner': partner,
            'COMPANY_INFO': COMPANY_INFO,
        }))

    # ----------------------------
    # DOWNLOAD PDF VIEW
    # ----------------------------
    def download_dc_pdf(self, request, order_id):
        order = Order.objects.get(pk=order_id)
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(220, height - 50, "DELIVERY CHALLAN")

        # Company Info
        p.setFont("Helvetica", 10)
        y = height - 90
        p.drawString(50, y, "From: Skylink Fibernet Private Limited")
        y -= 15
        p.drawString(50, y, "B6, II Floor, Vue Grande, 339 Chinnaswamy Road, Siddha Pudhur, Coimbatore - 641044")
        y -= 15
        p.drawString(50, y, "Email: info@skylink.net.in  |  Phone: (+91) 99441 99445")

        # Order Info
        y -= 30
        p.setFont("Helvetica-Bold", 11)
        p.drawString(50, y, f"Challan No: {order.dc_number or '-'}")
        p.drawString(250, y, f"Date: {order.created_at.strftime('%d-%m-%Y')}")
        y -= 15
        p.setFont("Helvetica", 10)
        p.drawString(50, y, "Mode of Transport: -")
        p.drawString(250, y, "Vehicle No: -")

        # Partner Info
        partner = getattr(order.user, 'partner', None)
        y -= 40
        p.setFont("Helvetica-Bold", 11)
        p.drawString(50, y, "To:")
        p.setFont("Helvetica", 10)
        y -= 15
        if partner:
            p.drawString(70, y, f"{partner.first_name} {partner.last_name}")
            y -= 15
            for line in (partner.address or '').split('\n'):
                p.drawString(70, y, line.strip())
                y -= 15
            if partner.phone:
                p.drawString(70, y, f"Phone: {partner.phone}")
                y -= 15
            if partner.code:
                p.drawString(70, y, f"Code: {partner.code}")
        else:
            p.drawString(70, y, "No partner address available")

        # Table Header
        y -= 30
        p.setFont("Helvetica-Bold", 11)
        p.drawString(50, y, "Item")
        p.drawString(250, y, "Qty")
        p.drawString(300, y, "Price")
        p.drawString(370, y, "Subtotal")
        p.drawString(460, y, "Serial No.")
        y -= 10
        p.line(50, y, 550, y)

        # Table Rows
        y -= 20
        p.setFont("Helvetica", 10)
        for item in order.orderitem_set.all():
            if y < 80:
                p.showPage()
                y = height - 50
            subtotal = item.price * item.quantity
            p.drawString(50, y, item.asset.name[:25])
            p.drawString(250, y, str(item.quantity))
            p.drawString(300, y, f"₹{item.price:.2f}")
            p.drawString(370, y, f"₹{subtotal:.2f}")
            # FIXED: Get serials from related model
            serials = ", ".join([s.serial_number for s in item.orderitemserial_set.all()])
            p.drawString(460, y, serials or "-")
            y -= 15

        # Total
        y -= 20
        p.setFont("Helvetica-Bold", 11)
        p.drawString(300, y, f"Total: ₹{order.amount:.2f}")

        # Footer
        y -= 50
        p.line(400, y, 550, y)
        y -= 10
        p.drawString(420, y, "Authorized Signature")

        p.showPage()
        p.save()
        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="DC_{order.dc_number or order.order_id}.pdf"'
        return response

    # ----------------------------
    # INLINE HTML SUMMARY (ADMIN DETAIL)
    # ----------------------------
    def order_summary(self, obj):
        items = obj.orderitem_set.all()
        if not items.exists():
            return "No items in this order."

        partner = getattr(obj.user, 'partner', None)
        to_address = f"""
        <strong>To:</strong><br>
        {partner.first_name if partner else ''} {partner.last_name if partner else ''}<br>
        {partner.address or 'Address not available'}<br>
        {partner.phone or ''}<br>
        Code: {partner.code or '-'}
        """ if partner else "<i>No partner found</i>"

        rows_html = ""
        for item in items:
            serials = ", ".join([s.serial_number for s in item.orderitemserial_set.all()])
            rows_html += f"""
                <tr>
                    <td>{item.asset.name}</td>
                    <td style='text-align:center'>{item.quantity}</td>
                    <td style='text-align:right'>₹{item.price:.2f}</td>
                    <td style='text-align:right'>₹{item.price * item.quantity:.2f}</td>
                    <td style='text-align:center'>{serials or '-'}</td>
                </tr>
            """

        total = sum(i.price * i.quantity for i in items)

        html = f"""
        <div style='margin-bottom:10px;padding:5px;background:#f9f9f9;border-radius:6px;'>
          <div style='display:flex;justify-content:space-between;'>
            <div>{COMPANY_INFO}</div>
            <div>{to_address}</div>
          </div>
          <p><strong>Challan No:</strong> {obj.dc_number or '-'}<br>
             <strong>Date:</strong> {obj.created_at.strftime('%d-%m-%Y')}<br>
             <strong>Mode of Transport:</strong> -<br>
             <strong>Vehicle No:</strong> -</p>
        </div>
        <table style='border-collapse:collapse;width:100%;margin-top:10px;font-size:13px;'>
          <tr style='background:#f0f0f0;font-weight:600;'>
            <th>Item</th><th>Qty</th><th>Price</th><th>Subtotal</th><th>Serial No.</th>
          </tr>
          {rows_html}
          <tr>
            <td colspan='4' style='text-align:right;font-weight:bold;border-top:2px solid #555;'>Total</td>
            <td style='text-align:right;font-weight:bold;border-top:2px solid #555;'>₹{total:.2f}</td>
          </tr>
        </table>
        <div style='margin-top:10px;text-align:right;'>
          <a href='/admin/order/summary/{obj.id}/pdf/' class='button'>Download DC PDF</a>
        </div>
        """
        return format_html(html)

    order_summary.short_description = "Delivery Challan"


# --------------------------------------------
# SEPARATE ADMIN FOR ORDER ITEMS & SERIALS
# --------------------------------------------
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'asset', 'quantity', 'price')
    search_fields = ('order__order_id', 'asset__name')
    inlines = [OrderItemSerialInline]


@admin.register(OrderItemSerial)
class OrderItemSerialAdmin(admin.ModelAdmin):
    list_display = ('order_item', 'serial_number', 'created_at')
    search_fields = ('serial_number', 'order_item__asset__name')
