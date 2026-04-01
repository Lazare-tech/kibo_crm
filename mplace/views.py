from django.shortcuts import redirect, render
from django.shortcuts import render, get_object_or_404

from inventory import models
from .models import Boutique, Categorie
# Create your views here.
from django.db.models import Q
from inventory.models import Product

from django.db.models import Q

# def home(request):
#     query = request.GET.get('q', '').strip()
#     cat_slug = request.GET.get('cat')
    
#     # On récupère tous les produits pour la grille principale
#     produits = Product.objects.filter(is_published=True).select_related('boutique', 'category')
#     # NOUVEAUTÉS : On récupère uniquement les 7 derniers pour le scroll horizontal
#     # On le fait AVANT les filtres pour que les nouveautés restent fixes même si on cherche
#     nouveaux_produits =  Product.objects.all().select_related('boutique').order_by('-date_ajout')[:7]

#     # 1. Filtre par catégorie (si présent)
#     if cat_slug:
#         produits = produits.filter(categorie__slug=cat_slug)
        
#     # 2. Recherche par texte
#     if query:
#         produits = produits.filter(
#             Q(nom__icontains=query) | 
#             Q(boutique__ville__icontains=query) |
#             Q(boutique__nom__icontains=query)
#         )
    
#     context = {
#         'produits': produits,
#         'nouveaux_produits': nouveaux_produits, # On passe les 7 ici
#         'current_cat': cat_slug,
#         'query': query,
#     }

#     if request.headers.get('HX-Request'):
#         return render(request, 'mplace/body/partials/product_list.html', context)
        
#     return render(request, 'mplace/body/index.html', context)
def home(request):
    query = request.GET.get('q', '').strip()
    cat_slug = request.GET.get('cat')
    
    # Correction : is_published=True et select_related('category')
    produits = Product.objects.filter(is_published=True).select_related('boutique', 'category').order_by('-date_added')
    
    # Correction : date_added au lieu de date_ajout
    nouveaux_produits = Product.objects.filter(is_published=True).select_related('boutique').order_by('-date_added')[:7]

    # 1. Filtre par catégorie (Correction : category__slug)
    if cat_slug:
        produits = produits.filter(category__slug=cat_slug)
        
    # 2. Recherche par texte (Correction : name__icontains)
    if query:
        produits = produits.filter(
            Q(name__icontains=query) | 
            Q(boutique__ville__icontains=query) |
            Q(boutique__nom__icontains=query)
        )
    
    context = {
        'produits': produits,
        'nouveaux_produits': nouveaux_produits,
        'current_cat': cat_slug,
        'query': query,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mplace/body/partials/product_list.html', context)
        
    return render(request, 'mplace/body/index.html', context)
def market(request):
    query = request.GET.get('q', '').strip()
    cat_slug = request.GET.get('cat')
    
    boutiques = Boutique.objects.all().order_by('nom')
    # CHANGEMENTS : 'category' au lieu de 'categorie' | 'date_added' au lieu de 'date_ajout'
    produits = Product.objects.filter(is_published=True).select_related('boutique', 'category').order_by('-date_added')
    categories = Categorie.objects.all()

    # Filtre par catégorie (Si présent)
    if cat_slug:
        # CHANGEMENT : category__slug au lieu de categorie__slug
        produits = produits.filter(category__slug=cat_slug)
        # CHANGEMENT : inventory_products__category__slug au lieu de produits__categorie__slug
        boutiques = boutiques.filter(inventory_products__category__slug=cat_slug).distinct()

    if query:
        # CHANGEMENT : inventory_products__name pour chercher dans les produits de la boutique
        boutiques = boutiques.filter(
            Q(nom__icontains=query) |
            Q(ville__icontains=query) |
            Q(inventory_products__name__icontains=query) 
        ).distinct()

        # CHANGEMENT : name__icontains au lieu de nom__icontains
        produits = produits.filter(
            Q(name__icontains=query) |
            Q(boutique__ville__icontains=query)
        )

    context = {
        'boutiques': boutiques,
        'produits': produits,
        'categories': categories,
        'query': query,
        'current_cat': cat_slug,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mplace/place/market_ui_fragment.html', context)
        
    return render(request, 'mplace/place/market.html', context)###
def detail_market(request, slug):
    boutique = get_object_or_404(Boutique, slug=slug)
    query = request.GET.get('q', '').strip()
    
    # On récupère les produits liés à cette boutique spécifique
    produits = boutique.inventory_products.filter(is_published=True).select_related('category')
    
    if query:
        produits = produits.filter(nom__icontains=query)
        
    context = {
        'boutique': boutique,
        'produits': produits
    }

    # Logique HTMX : si on recherche, on ne renvoie que le catalogue
    if request.headers.get('HX-Request'):
        return render(request, 'mplace/body/partials/product_catalogue_detail_market.html', context)

    return render(request, 'mplace/place/detail_market.html', context)

def contact(request):
    return render(request, 'mplace/body/contact.html')

############
from django.contrib.auth.forms import UserCreationForm
from django.views import View
from django.contrib import messages
class RegisterView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'registration/register.html', {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé pour {username} ! Vous pouvez vous connecter.')
            return redirect('mplace:login')
        return render(request, 'registration/register.html', {'form': form})
def logout(request):
    return redirect('mplace:home')
