from django.contrib import admin
from django.utils.html import format_html

from partner.models import PartnerAssetLimit
from .models import Asset, Category, Banner

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'asset_code', 'category', 'quantity', 'purchase_price', 'location', 'image_tag')
    search_fields = ('name', 'asset_code', 'location', 'category__name')  # search by category name

    list_filter = ('category',)  # filter by category in admin sidebar

    def image_tag(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html(f'<img src="{obj.image.url}" width="50" height="50" />')
        return "-"
    image_tag.short_description = 'Image'

# Optional: Register Category separately
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'description')
    search_fields = ('name', 'code')

from django.utils.html import format_html

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at', 'image_tag')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)

    def image_tag(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html('<img src="{}" width="100" />'.format(obj.image.url))
        return "-"
    image_tag.short_description = 'Banner Image'

