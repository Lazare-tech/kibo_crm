from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Categorie, Boutique, ProduitMarket

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug')

@admin.register(Boutique)
class BoutiqueAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville')
    search_fields = ('nom', 'ville')
    prepopulated_fields = {'slug': ('nom',)}

@admin.register(ProduitMarket)
class ProduitMarketAdmin(admin.ModelAdmin):
    list_display = ('nom', 'boutique', 'prix', 'categorie')
    list_filter = ('boutique', 'categorie')
    search_fields = ('nom', 'description')