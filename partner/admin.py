from django.contrib import admin
from .models import Partner, PartnerCategoryAssetLimit, PartnerCategory

# Unregister the default registration if it exists
try:
    admin.site.unregister(Partner)
except admin.sites.NotRegistered:
    pass



@admin.register(PartnerCategory)
class PartnerCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("user", "get_partner_category", "phone", "refundable_wallet")
    list_filter = ("partner_category",)
    search_fields = ("user__username", "first_name", "last_name")

    def get_partner_category(self, obj):
        return obj.partner_category.name if obj.partner_category else "-"
    get_partner_category.short_description = "Partner Category"

@admin.register(PartnerCategoryAssetLimit)
class PartnerCategoryAssetLimitAdmin(admin.ModelAdmin):
    list_display = (
        "partner_category_name",
        "asset_name",
        "default_limit",
        "created_at",
        "updated_at",
    )
    list_filter = ("partner_category__name", "asset__name")
    search_fields = ("partner_category__name", "asset__name")
    autocomplete_fields = ("partner_category", "asset")
    ordering = ("partner_category__name", "asset__name")

    def partner_category_name(self, obj):
        return obj.partner_category.name
    partner_category_name.short_description = "Partner Category"

    def asset_name(self, obj):
        return obj.asset.name
    asset_name.short_description = "Asset"
