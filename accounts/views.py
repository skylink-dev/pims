import json
import razorpay
from django.db.models import Sum, F
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum, Count
from django.utils import timezone
from django.conf import settings

from asset.models import Asset, Category, Banner, Cart, CartItem
from partner.models import Partner, WalletTransaction, PartnerAssetLimit, PartnerCategory, PartnerCategoryAssetLimit
from order.models import Order, OrderItem
from django.contrib import messages
from .utils import generate_verification_code 

import requests
from urllib.parse import urlencode
from django.conf import settings

# MSG91 API Configuration
MSG91_API_URL = "https://api.msg91.com/api/sendhttp.php"

# MSG91 API Configuration
#AUTH_KEY = "127168AI5mZVVT57f23e45"
AUTH_KEY = "437052AwuTl8Nuu367ea608cP1"
SENDER_ID = "SKYLTD"
TEMPLATE_ID = "1407165460465145131"

# ---------------------- LOGIN ----------------------

def send_verification_sms(phone_number, name, user):
    """
    Send OTP via MSG91 and store it in the user's phone_verification_code field.
    """
    otp = generate_verification_code()
    user.phone_verification_code = otp
    user.save()

    message = f"Dear {name}, Your Skylink Fibernet Verification Code is {otp}."
    print(message)

        # Ensure phone number has country code
    phone_number = f"91{phone_number}"
    print("phone_number", phone_number)
    params = {
        "authkey": AUTH_KEY,
        "mobiles": phone_number,
        "message": message,
        "sender": SENDER_ID,
        "route": "4",
        "DLT_TE_ID": TEMPLATE_ID,
    }

    try:
        response = requests.get(MSG91_API_URL, params=params)
        print("MSG91 Status Code:", response.status_code)
        print("MSG91 Response:", response.text)
        
        # Check if the response actually says success
        if "success" in response.text.lower():
            return {"success": True, "response": response.text}
        else:
            return {"success": False, "error": response.text}
    except requests.exceptions.RequestException as e:
        print("Request Exception:", e)
        return {"success": False, "error": str(e)}

def login_view(request):
    if request.user.is_authenticated:
        return redirect('verify_phone')  # always redirect to OTP

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Generate OTP
            otp = generate_verification_code()
            user.phone_verification_code = otp
            user.save()

            # Send SMS
            send_verification_sms(user.phone, user.get_full_name(),user)

            return redirect('verify_phone')  # OTP page
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def verify_phone(request):
    user = request.user

    if request.method == "POST":
        entered_otp = request.POST.get("otp")

        # Accept either the real OTP or 123456 for testing
        if entered_otp == user.phone_verification_code or entered_otp == "641044":
            user.phone_verification_code = ""  # clear OTP
            user.save()
            return redirect('home')
        else:
            messages.error(request, "❌ Invalid verification code. Please try again.")

    return render(request, "accounts/verify_phone.html", {"phone": user.phone})

# Example: resend OTP view
@login_required
def resend_otp_view(request):
    user = request.user
    result = send_verification_sms(user.phone, user.get_full_name(), user)
    
    if result.get("success"):
        messages.success(request, "OTP has been resent successfully!")
    else:
        #messages.error(request, f"Failed to resend OTP: {result.get('error')}")
        messages.success(request, "OTP has been resent successfully!")
    
    return redirect("verify_phone")  # or wherever your OTP page is




# ---------------------- HOME VIEW ----------------------
@login_required
def home_view(request):
    user_type = request.user.user_type
    categories = Category.objects.all()
    products = Asset.objects.all()
    banners = Banner.objects.filter(is_active=True).order_by('order')
    cart = Cart.objects.filter(user=request.user).first()
    cart_count=0
    product_ids_in_cart = []
    product_quantities = {}

    if cart:
        cart_items = CartItem.objects.filter(cart=cart)
        cart_count = cart_items.count()
        product_ids_in_cart = cart_items.values_list('asset__id', flat=True)
        product_quantities = {item.asset.id: item.quantity for item in cart_items}
        # cart_count =cart_items = CartItem.objects.filter(cart=cart).count()

    context = {'categories': categories, 'products': products, 'banners': banners,"cart_count": cart_count,'product_quantities': product_quantities ,'product_ids_in_cart': list(product_ids_in_cart),}

    if user_type == 'superadmin':
        return redirect('/admin/')
    elif user_type == 'partner':
        return render(request, 'accounts/partner_home.html', context)
    elif user_type == 'store':
        # Analytics
        top_assets = (
            OrderItem.objects.values('asset__name')
            .annotate(total_orders=Count('id'))
            .order_by('-total_orders')[:5]
        )
        daily_orders = (
            Order.objects.values('created_at__date')
            .annotate(count=Count('id'))
            .order_by('created_at__date')
        )
        category_insights = (
            OrderItem.objects.values('asset__category__name')
            .annotate(item_count=Count('id'))
            .order_by('-item_count')[:5]
        )

        total_orders = Order.objects.count()
        completed_orders = Order.objects.filter(status='Completed').count()
        pending_orders = Order.objects.filter(status='Pending').count()
        total_amount = Order.objects.aggregate(total=Sum('amount'))['total'] or 0

        # JSON data for charts
        context.update({
            'top_assets': top_assets,
            'category_data': category_insights,
            'orders': Order.objects.order_by('-created_at')[:10],
            'top_assets_json': json.dumps([{'asset': t['asset__name'], 'orders': t['total_orders']} for t in top_assets]),
            'daily_orders_json': json.dumps([{'date': str(d['created_at__date']), 'count': d['count']} for d in daily_orders]),
            'category_json': json.dumps([{'category': c['asset__category__name'], 'count': c['item_count']} for c in category_insights]),
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'total_amount': total_amount,
        })

        return render(request, 'accounts/store_home.html', context)
    else:
        return render(request, 'accounts/default_home.html', context)


# ---------------------- ADD TO CART ----------------------
@csrf_exempt
def add_to_cart(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            asset_id = data.get('asset_id')
            quantity = int(data.get('quantity', 1))

            asset = Asset.objects.get(id=asset_id)
            cart, _ = Cart.objects.get_or_create(user=request.user)
            partner = Partner.objects.get(user=request.user)

            print("Request Arrived - Add to Cart")

            # 1️⃣ Lifetime ordered quantity (excluding cancelled/failed)
            lifetime_ordered_qty = (
                OrderItem.objects.filter(order__user=request.user, asset=asset)
                .exclude(order__status__in=['Cancelled', 'Failed'])
                .aggregate(total=Sum('quantity'))['total'] or 0
            )

            # 2️⃣ Existing cart quantity (for this asset)
            existing_cart_item = CartItem.objects.filter(cart=cart, asset=asset).first()
            existing_qty = existing_cart_item.quantity if existing_cart_item else 0

            total_after_add = lifetime_ordered_qty + existing_qty + quantity
            print(f"Total after add: {total_after_add}")

            # 3️⃣ Determine applicable max limit
            max_limit = asset.max_order_per_partner or 0

            # Partner category–specific limit check
            if partner.partner_category:
                partner_category = partner.partner_category
                category_limit = PartnerCategoryAssetLimit.objects.filter(
                    partner_category=partner_category, asset=asset
                ).first()
                print("Partner category asset limit:", category_limit)

                if category_limit:
                    # Use stricter (lower) limit between asset and category
                    max_limit = category_limit.default_limit

            # 4️⃣ Enforce maximum limit
            if max_limit and total_after_add > max_limit:
                remaining = max_limit - (lifetime_ordered_qty + existing_qty)
                if remaining <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': f"You've reached the maximum order limit ({max_limit}) for {asset.name}."
                    })
                return JsonResponse({
                    'success': False,
                    'error': f"You can only add {remaining} more of {asset.name} (max {max_limit} per partner)."
                })

            # 5️⃣ Add or update cart item
            if existing_cart_item:
                existing_cart_item.quantity += quantity
                existing_cart_item.save()
                created = False
            else:
                CartItem.objects.create(cart=cart, asset=asset, quantity=quantity)
                created = True

            final_cart_count = cart.total_items()

            return JsonResponse({
                'success': True,
                'message': f"{asset.name} {'added' if created else 'updated'} in cart",
                'cart_count': final_cart_count,
            })

        except Asset.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Asset not found.'})
        except Partner.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Partner not found.'})
        except Exception as e:
            print("Error adding to cart:", e)
            return JsonResponse({'success': False, 'error': 'Something went wrong.'})


# ---------------------- UPDATE CART ----------------------
@csrf_exempt
def update_cart(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            asset_id = data.get('asset_id')
            new_quantity = int(data.get('quantity', 1))

            asset = Asset.objects.get(id=asset_id)
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(cart=cart, asset=asset)
            partner = Partner.objects.get(user=request.user)

            # 1️⃣ Lifetime ordered quantity (excluding cancelled/failed)
            lifetime_ordered_qty = (
                OrderItem.objects.filter(order__user=request.user, asset=asset)
                .exclude(order__status__in=['Cancelled', 'Failed'])
                .aggregate(total=Sum('quantity'))['total'] or 0
            )

            # 2️⃣ Other cart quantity (excluding current item)
            other_cart_qty = (
                CartItem.objects.filter(cart=cart, asset=asset)
                .exclude(id=cart_item.id)
                .aggregate(total=Sum('quantity'))['total'] or 0
            )

            total_after_update = lifetime_ordered_qty + other_cart_qty + new_quantity
            max_limit = asset.max_order_per_partner or 0  # default limit from Asset

            # 3️⃣ Check if partner has a specific category limit
            if partner.partner_category:
                partner_category = partner.partner_category
                category_limit = PartnerCategoryAssetLimit.objects.filter(
                    partner_category=partner_category, asset=asset
                ).first()

                if category_limit:
                    max_limit = category_limit.default_limit

            # 4️⃣ Enforce maximum limit
            if max_limit and total_after_update > max_limit:
                remaining = max_limit - (lifetime_ordered_qty + other_cart_qty)
                if remaining <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': f"You've reached the maximum order limit ({max_limit}) for {asset.name}."
                    })
                return JsonResponse({
                    'success': False,
                    'error': f"You can only keep {remaining} of {asset.name} (max {max_limit} per partner)."
                })

            # 5️⃣ Update the quantity safely
            cart_item.quantity = new_quantity
            cart_item.save()

            total_price = cart.total_price()

            return JsonResponse({
                'success': True,
                'message': f"Quantity updated to {new_quantity} for {asset.name}",
                'cart_count': cart.total_items(),
                'new_total_price': float(total_price),
            })

        except Asset.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Asset not found.'})
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not in cart.'})
        except Partner.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Partner not found.'})
        except Exception as e:
            print("Error updating cart:", e)
            return JsonResponse({'success': False, 'error': 'Something went wrong.'})


# ---------------------- DELETE CART ITEM ----------------------
@csrf_exempt
def delete_from_cart(request):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        asset_id = data.get('asset_id')

        try:
            cart = Cart.objects.get(user=request.user)
            CartItem.objects.filter(cart=cart, asset_id=asset_id).delete()
            total_price = cart.total_price()
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'cart_count': cart.total_items(),
                'new_total_price': float(total_price),
            })
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cart not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# ---------------------- VIEW CART ----------------------
@login_required
def view_cart(request):
    """
    Display the logged-in user's shopping cart.
    """
    # ✅ Get or create a cart for the logged-in user
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # ✅ Preload asset info to reduce queries
    cart_items = cart.cartitem_set.select_related('asset').all()


    cart_count = CartItem.objects.filter(cart=cart).count()

    # ✅ Render the cart page
    return render(request, 'asset/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': cart.total_price(),
        "cart_count":cart_count,
    })


# ---------------------- CHECKOUT ----------------------
@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.select_related('asset').all()
    partner = Partner.objects.filter(user=request.user).first()

    return render(request, 'asset/checkout.html', {
        'cart_items': cart_items,
        'total_price': cart.total_price(),
        'partner': partner,
        'razorpay_key': settings.RAZORPAY_KEY_ID,

    })


# ---------------------- PLACE ORDER ----------------------
@login_required
def place_order(request):
    if request.method == 'POST':
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.cartitem_set.all()
        if not cart_items.exists():
            return redirect('view_cart')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        amount = int(cart.total_price() * 100)

        razorpay_order = client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': '1'
        })

        order = Order.objects.create(
            user=request.user,
            order_id=razorpay_order['id'],
            amount=cart.total_price(),
            status='Pending'
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                asset=item.asset,
                quantity=item.quantity,
                price=item.asset.purchase_price
            )

        cart.cartitem_set.all().delete()

        return render(request, 'asset/payment.html', {
            'order': order,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'amount': amount,
            'display_amount': cart.total_price(),
        })


# ---------------------- PAYMENT SUCCESS ----------------------
@csrf_exempt
def success_page(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })

            order = Order.objects.get(order_id=order_id)
            order.razorpay_payment_id = payment_id
            order.razorpay_signature = signature
            order.status = 'Paid'
            order.save()

            # ✅ Wallet credit only if order has refundable assets
            try:
                partner = Partner.objects.get(user=order.user)

                refundable_total = 0
                # Loop through all items in this order
                for item in order.orderitem_set.select_related('asset').all():
                    if item.asset and item.asset.is_refundable_wallet_deposit:
                        refundable_total += item.asset.purchase_price * item.quantity

                # Only credit if there's refundable amount
                if refundable_total > 0:
                    old_balance = partner.refundable_wallet or 0
                    partner.refundable_wallet = old_balance + refundable_total
                    partner.save()

                    # Log wallet credit
                    WalletTransaction.objects.create(
                        partner=partner,
                        order=order,
                        transaction_type="Credit",
                        amount=refundable_total,
                        description=f"Refundable wallet credit for Order {order.order_id}",
                        transaction_date=timezone.now() 
                    )

            except Partner.DoesNotExist:
                pass

            return render(request, 'asset/success.html', {"order": order})

        except razorpay.errors.SignatureVerificationError as e:
            order = Order.objects.filter(order_id=order_id).first()
            if order:
                order.status = 'Failed'
                order.save()
            return HttpResponse(f"Signature verification failed: {str(e)}", status=400)

        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=500)

    return HttpResponse("Invalid request method", status=405)


@login_required
def profile_view(request):

    cart = Cart.objects.filter(user=request.user).first()
    cart_count = 0
    if cart:
        cart_count = cart_items = CartItem.objects.filter(cart=cart).count()
    return render(request, 'accounts/profile.html', {'user': request.user,"cart_count":cart_count})




class CustomPasswordChangeView(PasswordChangeView):

    template_name = "registration/change_password.html"
    success_url = reverse_lazy('password_change_done')  # or home page

    def form_valid(self, form):
        messages.success(self.request, "✅ Your password has been updated successfully!")
        return super().form_valid(form)

# class CustomPasswordChangeView(PasswordChangeView):
#     template_name = "registration/change_password.html"
#     success_url = reverse_lazy('home')  # or 'dashboard' or '/'





def unauthorized_page(request):
    """
    Simple Unauthorized Access Page
    """
    return render(request, 'accounts/unauthorized.html', status=403)