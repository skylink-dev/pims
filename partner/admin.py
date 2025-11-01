from django.contrib import admin
from .models import Partner, PartnerAssetLimit

# Unregister the default registration if it exists
try:
    admin.site.unregister(Partner)
except admin.sites.NotRegistered:
    pass

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "code", "refundable_wallet")
    search_fields = ("user__username", "first_name", "last_name", "code")




@admin.register(PartnerAssetLimit)
class PartnerAssetLimitAdmin(admin.ModelAdmin):
    list_display = (
        "partner_name",
        "asset_name",
        "max_purchase_limit",
        "created_at",
        "updated_at",
    )
    list_filter = ("partner__user__username", "asset__name", "partner__partner_category")
    search_fields = (
        "partner__user__username",
        "asset__name",
    )
    autocomplete_fields = ("partner", "asset")
    ordering = ("partner__user__username", "asset__name")

    def partner_name(self, obj):
        """Display partner username with category, e.g. 'john_doe (Gold)'."""
        username = obj.partner.user.username
        category = obj.partner.get_partner_category_display()  # human-readable value
        return f"{username} ({category})"

    partner_name.short_description = "Partner (Category)"

    def asset_name(self, obj):
        return obj.asset.name

    asset_name.short_description = "Asset"
