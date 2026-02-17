from django.contrib import admin
from .models import Category, OrderLine, Product, StockMovement, Supplier, SupplierOrder
from django.utils.html import format_html
from django.db import transaction

# 1. Configuration des produits (Déjà bien, j'ajoute juste search_fields pour l'autocomplete)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'colored_quantity', 'selling_price', 'unit')
    list_filter = ('category', 'unit')
    search_fields = ('name', 'sku') # CRUCIAL pour l'autocomplete dans les commandes
    list_editable = ('selling_price',)

    def colored_quantity(self, obj):
        if obj.is_low_stock:
            return format_html('<span style="color: #d9534f; font-weight: bold;">{} <i class="fas fa-exclamation-triangle"></i></span>', obj.quantity)
        return format_html('<span style="color: #5cb85c; font-weight: bold;">{}</span>', obj.quantity)
    colored_quantity.short_description = "Stock Actuel"

# 2. Inlines pour les lignes de commande
class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 1
    autocomplete_fields = ['product'] # Fonctionne grâce au search_fields de ProductAdmin

# 3. Configuration de la Commande Fournisseur
@admin.register(SupplierOrder)
class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'status', 'date_order', 'total_amount_display')
    list_filter = ('status', 'supplier', 'date_order')
    search_fields = ('order_number', 'supplier__name')
    readonly_fields = ('order_number', 'total_amount') # On ne modifie pas le total à la main
    inlines = [OrderLineInline]

    def total_amount_display(self, obj):
        return format_html('<b>{} F</b>', obj.total_amount)
    total_amount_display.short_description = "Montant Total"

    @transaction.atomic
    def save_related(self, request, form, formsets, change):
        # 1. On enregistre d'abord les lignes en base
        super().save_related(request, form, formsets, change)
        
        # 2. On appelle le moteur du modèle
        instance = form.instance
        instance.process_stock_reception(user=request.user)

# 4. Enregistrement des modèles simples (avec sécurité AlreadyRegistered)
if not admin.site.is_registered(Category):
    admin.site.register(Category)

if not admin.site.is_registered(StockMovement):
    admin.site.register(StockMovement)

if not admin.site.is_registered(Supplier):
    admin.site.register(Supplier)