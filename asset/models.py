from django.db import models
from django.conf import settings


from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)  # name is not unique
    code = models.CharField(max_length=50, unique=True)  # unique code for category
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/images/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"



class Asset(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='assets/images/', blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    asset_code = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=100, blank=True, null=True)

    # 🆕 New Fields
    is_refundable_wallet_deposit = models.BooleanField(
        default=False,
        help_text="Mark this asset as a refundable wallet deposit item."
    )

    max_order_per_partner = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Optional: Set a limit if this asset should have a max order restriction per partner."
    )
    
    def __str__(self):
        return f"{self.name} ({self.asset_code})"



class Banner(models.Model):
    title = models.CharField(max_length=150, default='Default Banner Title')
    description = models.TextField(blank=True, null=True, default='This is a default banner description.')
    image = models.ImageField(upload_to='banners/', default='banners/default.jpg')  # make sure default image exists in media
    order = models.PositiveIntegerField(default=1, help_text="Lower numbers appear first")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']  # always order by the 'order' field

    def __str__(self):
        return self.title
    
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def total_items(self):
        # Count total quantity (not just distinct assets)
        return sum(item.quantity for item in self.cartitem_set.all())

    def total_price(self):
        return sum(item.asset.purchase_price * item.quantity for item in self.cartitem_set.all())

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    class Meta:
        unique_together = ('cart', 'asset')  # ✅ Enforce unique pair
    def __str__(self):
        return f"{self.quantity} x {self.asset.name}"