from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from asset.models import Asset, Category , Banner, Cart, CartItem
from django.shortcuts import redirect, get_object_or_404
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Count total items from CartItem
    cart_count = CartItem.objects.filter(cart=cart).count()
    context = {
        'categories': categories,
        'products': products,
        'banners': banners,
        'cart_count': cart_count,
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


# Update quantity of an asset in cart
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
                'cart_count': cart.total_items()
            })
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Item not in cart'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# Delete an asset from the cart
@csrf_exempt
def delete_from_cart(request):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        asset_id = data.get('asset_id')

        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(cart=cart, asset_id=asset_id)
            cart_item.delete()

            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'cart_count': cart.total_items()
            })
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Item not in cart'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# View cart
@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.select_related('asset').all()
    total_price = sum(item.asset.purchase_price * item.quantity for item in cart_items)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price
    }
    return render(request, 'asset/cart.html', context)