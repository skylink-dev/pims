from accounts.models import CustomUser
from django.utils import timezone
from django.db import models

from django.conf import settings

class PartnerCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Partner Category"
        verbose_name_plural = "Partner Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Partner(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, default='John')
    last_name = models.CharField(max_length=50, default='Doe')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    partner_category = models.ForeignKey(
        PartnerCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='partners',
        help_text="Category of the partner (e.g., Platinum, Gold, Silver)"
    )
    code = models.CharField(max_length=50, blank=True, null=True)
    refundable_wallet = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Refundable wallet balance for this partner"
    )

    def __str__(self):
        category_name = self.partner_category.name if self.partner_category else "No Category"
        return f"{self.user.username} ({category_name})"
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



class PartnerCategoryAssetLimit(models.Model):
    partner_category = models.ForeignKey(
        "partner.PartnerCategory",
        on_delete=models.CASCADE,
        related_name="asset_limits",
        help_text="Partner category for which this limit applies."
    )
    asset = models.ForeignKey(
        "asset.Asset",
        on_delete=models.CASCADE,
        related_name="category_limits",
        help_text="Asset for which the limit applies."
    )
    default_limit = models.PositiveIntegerField(
        default=0,
        help_text="Default maximum quantity for this asset based on category."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("partner_category", "asset")
        verbose_name = "Partner Category Asset Limit"
        verbose_name_plural = "Partner Category Asset Limits"
        ordering = ["partner_category__name", "asset__name"]

    def __str__(self):
        return f"{self.partner_category.name} - {self.asset.name} (Default: {self.default_limit})"
