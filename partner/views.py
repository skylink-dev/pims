from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from asset.models import CartItem,Cart
from .models import Partner, WalletTransaction

@login_required
def wallet_view(request):
    """
    Show the partner's refundable wallet and transaction history.
    """
    partner = get_object_or_404(Partner, user=request.user)
    transactions = partner.wallet_transactions.all().order_by('-transaction_date')

    cart = Cart.objects.filter(user=request.user).first()
    cart_count = 0

    if cart:
        cart_count = cart_items = CartItem.objects.filter(cart=cart).count()

    context = {
        'partner': partner,
        'transactions': transactions,
        'cart_count':cart_count,
    }
    return render(request, 'partner/wallet.html', context)
