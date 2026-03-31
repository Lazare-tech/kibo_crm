from django.shortcuts import redirect, render
from django.shortcuts import render, get_object_or_404

from inventory import models
from .models import Boutique, ProduitMarket, Categorie
# Create your views here.
from django.db.models import Q

from django.db.models import Q

def home(request):
    query = request.GET.get('q', '').strip()
    cat_slug = request.GET.get('cat')
    
    # On récupère tous les produits pour la grille principale
    produits = ProduitMarket.objects.all().select_related('boutique', 'categorie').order_by('-date_ajout')
    
    # NOUVEAUTÉS : On récupère uniquement les 7 derniers pour le scroll horizontal
    # On le fait AVANT les filtres pour que les nouveautés restent fixes même si on cherche
    nouveaux_produits = ProduitMarket.objects.all().select_related('boutique').order_by('-date_ajout')[:7]

    # 1. Filtre par catégorie (si présent)
    if cat_slug:
        produits = produits.filter(categorie__slug=cat_slug)
        
    # 2. Recherche par texte
    if query:
        produits = produits.filter(
            Q(nom__icontains=query) | 
            Q(boutique__ville__icontains=query) |
            Q(boutique__nom__icontains=query)
        )
    
    context = {
        'produits': produits,
        'nouveaux_produits': nouveaux_produits, # On passe les 7 ici
        'current_cat': cat_slug,
        'query': query,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mplace/body/partials/product_list.html', context)
        
    return render(request, 'mplace/body/index.html', context)
def market(request):
    query = request.GET.get('q', '').strip()
    cat_slug = request.GET.get('cat') # On récupère la catégorie
    
    boutiques = Boutique.objects.all().order_by('nom')
    produits = ProduitMarket.objects.all().select_related('boutique', 'categorie').order_by('-date_ajout')
    categories = Categorie.objects.all()

    # Filtre par catégorie (Si présent)
    if cat_slug:
        produits = produits.filter(categorie__slug=cat_slug)
        # Optionnel : filtrer aussi les boutiques qui ont cette catégorie
        boutiques = boutiques.filter(produits__categorie__slug=cat_slug).distinct()

    if query:
        boutiques = boutiques.filter(
            Q(nom__icontains=query) |
            Q(ville__icontains=query) |
            Q(produits__nom__icontains=query)
        ).distinct()

        produits = produits.filter(
            Q(nom__icontains=query) |
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
        
    return render(request, 'mplace/place/market.html', context)
###
def detail_market(request, slug):
    boutique = get_object_or_404(Boutique, slug=slug)
    query = request.GET.get('q', '').strip()
    
    # On récupère les produits liés à cette boutique spécifique
    produits = boutique.produits.all().select_related('categorie')
    
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
