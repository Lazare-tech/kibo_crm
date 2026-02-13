
# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Sale, SaleItem,Payment

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('total_line',)
    fields = ('product', 'quantity', 'unit_price', 'total_line')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    # Affichage dans la liste principale
    list_display = ('sale_number', 'client', 'date', 'colored_total', 'colored_status', 'view_pdf_link')
    list_filter = ('status', 'date', 'client')
    search_fields = ('sale_number', 'client__first_name', 'client__last_name', 'client__phone')
    ordering = ('-date',)
    
    # Intégration des articles de vente directement dans la fiche de vente
    inlines = [SaleItemInline]
    
    # Organisation des champs dans le formulaire d'édition
    fieldsets = (
        ("Informations Générales", {
            'fields': ('sale_number', 'client', 'date')
        }),
        ("Finances", {
            'fields': (('total_amount', 'amount_paid'), 'status'),
        }),
    )
    readonly_fields = ('sale_number', 'date')

    # --- MÉTHODES PERSONNALISÉES POUR L'AFFICHAGE ---

    def colored_total(self, obj):
        return format_html('<span style="font-weight: bold;">{} F</span>', obj.total_amount)
    colored_total.short_description = "Montant Total"

    def colored_status(self, obj):
        # On ajoute des couleurs selon le statut
        colors = {
            'paye': '#28a745',       # Vert
            'partiel': '#ffc107',    # Jaune/Orange
            'en_attente': '#dc3545', # Rouge
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    colored_status.short_description = "État du paiement"

    def view_pdf_link(self, obj):
        # Remplace 'generate-invoice-pdf' par le nom exact de ton URL PDF
        try:
            url = reverse('sales:generate-invoice-pdf', args=[obj.id])
            return format_html('<a class="button" href="{}" target="_blank" style="background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 4px;">📥 PDF</a>', url)
        except:
            return "Indisponible"
    view_pdf_link.short_description = "Action"
    ######
# Permet d'ajouter/voir des paiements directement dans la fiche d'une vente
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1 # Propose une ligne vide pour un nouveau versement
    readonly_fields = ('date_payment',)
    fields = ('amount', 'payment_method', 'date_payment')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    # Liste principale des versements
    list_display = ('sale_link', 'colored_amount', 'payment_method', 'date_payment')
    list_filter = ('payment_method', 'date_payment')
    search_fields = ('sale__sale_number', 'sale__client__first_name', 'sale__client__last_name')
    date_hierarchy = 'date_payment' # Ajoute une barre de navigation par date en haut
    
    # Empêcher la modification d'un paiement déjà enregistré pour la sécurité comptable
    # readonly_fields = ('sale', 'amount', 'date_payment', 'payment_method')

    def sale_link(self, obj):
        # Crée un lien vers la vente correspondante
        return format_html('<a href="/admin/sales/sale/{}/change/">{}</a>', obj.sale.id, obj.sale.sale_number)
    sale_link.short_description = "N° Facture"

    def colored_amount(self, obj):
        return format_html('<span style="color: #28a745; font-weight: bold;">+ {} F</span>', obj.amount)
    colored_amount.short_description = "Montant versé"