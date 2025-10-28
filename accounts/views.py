from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from asset.models import Asset, Category , Banner, Cart, CartItem
from django.shortcuts import redirect, get_object_or_404
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from partner.models import Partner 


from django.contrib.auth.decorators import login_required
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def home_view(request):
    user_type = request.user.user_type

    # Fetch categories, products, and active banners
    categories = Category.objects.all()
    products = Asset.objects.all()
    banners = Banner.objects.filter(is_active=True).order_by('order')

    context = {
        'categories': categories,
        'products': products,
        'banners': banners,
    }

    if user_type == 'superadmin':
        return render(request, 'accounts/superadmin_home.html', context)
    elif user_type == 'partner':
        return render(request, 'accounts/partner_home.html', context)
    elif user_type == 'store':
        return render(request, 'accounts/store_home.html', context)
    else:
        return render(request, 'accounts/default_home.html', context)

# Add to cart or increase quantity
@csrf_exempt
def add_to_cart(request):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        asset_id = data.get('asset_id')
        quantity = int(data.get('quantity', 1))  # default 1 if not provided

        try:
            asset = Asset.objects.get(id=asset_id)
            cart, created = Cart.objects.get_or_create(user=request.user)

            cart_item, item_created = CartItem.objects.get_or_create(cart=cart, asset=asset)
            if not item_created:
                # If already in cart, increase quantity
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            cart_item.save()

            return JsonResponse({
                'success': True,
                'message': f"{asset.name} added to cart",
                'cart_count': cart.total_items()
            })
        except Asset.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Asset not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Add to cart or increase quantity
@csrf_exempt
def add_to_cart(request):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        asset_id = data.get('asset_id')
        quantity = int(data.get('quantity', 1))

        try:
            asset = Asset.objects.get(id=asset_id)
            cart, _ = Cart.objects.get_or_create(user=request.user)

            cart_item, created = CartItem.objects.get_or_create(cart=cart, asset=asset)
            if not created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            cart_item.save()

            return JsonResponse({
                'success': True,
                'message': f"{asset.name} added to cart",
                'cart_count': cart.total_items(),
            })

        except Asset.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Asset not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# Update quantity
@csrf_exempt
def update_cart(request):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        asset_id = data.get('asset_id')
        quantity = int(data.get('quantity', 1))

        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(cart=cart, asset_id=asset_id)
            cart_item.quantity = quantity
            cart_item.save()

            return JsonResponse({
                'success': True,
                'message': f"Quantity updated to {quantity}",
                'cart_count': cart.total_items(),
            })
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Item not in cart'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# Delete from cart
@csrf_exempt
def delete_from_cart(request):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        asset_id = data.get('asset_id')

        try:
            cart = Cart.objects.get(user=request.user)
            CartItem.objects.filter(cart=cart, asset_id=asset_id).delete()

            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'cart_count': cart.total_items(),
            })
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cart not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# View cart
@login_required
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.select_related('asset').all()

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': cart.total_price(),
    }
    return render(request, 'asset/cart.html', context)

from partner.models import Partner
from django.conf import settings
import razorpay
from order.models import Order, OrderItem
@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.select_related('asset').all()
    
    partner = Partner.objects.filter(user=request.user).first()
    
    context = {
        'cart_items': cart_items,
        'total_price': cart.total_price(),
        'partner': partner,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'asset/checkout.html', context)


@login_required
def place_order(request):
    if request.method == 'POST':
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.cartitem_set.all()

        if not cart_items.exists():
            return redirect('view_cart')

        # create Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        amount = int(cart.total_price() * 100)  # Razorpay amount in paise

        # create Razorpay order
        razorpay_order = client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': '1'
        })

        # create Order object in DB
        order = Order.objects.create(
            user=request.user,
            order_id=razorpay_order['id'],
            amount=cart.total_price(),
            status='Pending'
        )

        # create OrderItems for each cart item
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                asset=item.asset,
                quantity=item.quantity,
                price=item.asset.purchase_price
            )

        # Optionally clear cart after placing order
        cart.cartitem_set.all().delete()

        return render(request, 'asset/payment.html', {
            'order': order,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'amount': amount,
            'display_amount': cart.total_price(),
        })
    


from django.views.decorators.csrf import csrf_exempt
import razorpay
from django.shortcuts import redirect


from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.utils import timezone
import razorpay
from django.conf import settings
from order.models import Order
from partner.models import Partner, WalletTransaction  # ✅ Make sure WalletTransaction model exists


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

            # ✅ Add amount to partner’s refundable wallet
            try:
                partner = Partner.objects.get(user=order.user)
                
                # update partner refundable wallet balance
                partner.refundable_wallet = (partner.refundable_wallet or 0) + order.amount
                partner.save()

                # create wallet transaction record
                WalletTransaction.objects.create(
                    partner=partner,
                    order=order,
                    transaction_type="Credit",
                    amount=order.amount,
                    description=f"Refundable wallet credit for Order {order.order_id}",
                    transaction_date=timezone.now().date()
                )

            except Partner.DoesNotExist:
                pass  # If no partner, skip wallet credit

            # ✅ Show success popup page
            return render(request, 'asset/success.html', {"order": order})

        except razorpay.errors.SignatureVerificationError:
            order = Order.objects.filter(order_id=order_id).first()
            if order:
                order.status = 'Failed'
                order.save()
            return redirect('home')

    return redirect('home')
