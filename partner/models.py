from accounts.models import CustomUser
from django.utils import timezone
from django.db import models

class Partner(models.Model):

    CATEGORY_CHOICES = [
        ('platinum', 'Platinum'),
        ('gold', 'Gold'),
        ('silver', 'Silver'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, default='John')
    last_name = models.CharField(max_length=50, default='Doe')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    partner_category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        default='silver',
        help_text="Category of the partner (Platinum, Gold, Silver)"
    )
    code = models.CharField(max_length=20, blank=True, null=True)
    refundable_wallet = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Refundable wallet balance for this partner"
    )

    
    def __str__(self):
        category = self.get_partner_category_display()
        return f"{self.user.username} ({category})"



class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ("Credit", "Credit"),
        ("Debit", "Debit"),
    )

    partner = models.ForeignKey(
        "partner.Partner",
        on_delete=models.CASCADE,
        related_name="wallet_transactions",
        null=True,
        blank=True
    )
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
        default="Credit",
        null=True,
        blank=True
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        null=True,
        blank=True
    )
    description = models.TextField(
        blank=True,
        null=True,
        default=""
    )
    transaction_date = models.DateTimeField(
        default=timezone.now,
        null=True,
        blank=True
    )

    def __str__(self):
        partner_name = self.partner.user.username if self.partner else "Unknown"
        return f"{self.transaction_type} - ₹{self.amount} ({partner_name})"

    class Meta:
        ordering = ["-transaction_date"]


from django.db import models

class PartnerAssetLimit(models.Model):
    partner = models.ForeignKey(
        "partner.Partner",
        on_delete=models.CASCADE,
        related_name="asset_limits"
    )
    asset = models.ForeignKey(
        "asset.Asset",
        on_delete=models.CASCADE,
        related_name="partner_limits"
    )
    max_purchase_limit = models.PositiveIntegerField(
        default=0,
        help_text="Maximum quantity of this asset that the partner can purchase."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("partner", "asset")
        verbose_name = "Partner Asset Limit"
        verbose_name_plural = "Partner Asset Limits"

    def __str__(self):
        return f"{self.partner.user.username} - {self.asset.name} Limit: {self.max_purchase_limit}"


