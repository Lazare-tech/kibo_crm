from django.contrib import admin

# Register your models here.
from .models import Category, Product, StockMovement
from django.utils.html import format_html

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'colored_quantity', 'selling_price', 'unit')
    list_filter = ('category', 'unit')
    search_fields = ('name', 'sku')
    list_editable = ('selling_price',)

    def colored_quantity(self, obj):
        if obj.is_low_stock:
            return format_html('<b style="color: red;">{} (Alerte !)</b>', obj.quantity)
        return format_html('<b style="color: green;">{}</b>', obj.quantity)
    colored_quantity.short_description = "Stock"

admin.site.register(Category)
admin.site.register(StockMovement)