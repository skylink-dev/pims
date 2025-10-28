from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Partner, WalletTransaction

@login_required
def wallet_view(request):
    """
    Show the partner's refundable wallet and transaction history.
    """
    partner = get_object_or_404(Partner, user=request.user)
    transactions = partner.wallet_transactions.all().order_by('-transaction_date')

    context = {
        'partner': partner,
        'transactions': transactions,
    }
    return render(request, 'partner/wallet.html', context)
