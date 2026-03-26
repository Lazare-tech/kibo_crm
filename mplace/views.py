from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Boutique, ProduitMarket, Categorie
# Create your views here.
def home(request):
    query = request.GET.get('q')
    produits = ProduitMarket.objects.all().order_by('-date_ajout')
    
    if query:
        produits = produits.filter(nom__icontains=query) | produits.filter(boutique__ville__icontains=query)
        
    context={
        'produits': produits
    }
    return render(request, 'mplace/body/index.html', context)


def market_list(request):
    ville_filter = request.GET.get('ville')
    boutiques = Boutique.objects.all()
    
    if ville_filter:
        boutiques = boutiques.filter(ville__icontains=ville_filter)
        
    context={
        'boutiques': boutiques
    }
    return render(request, 'mplace/place/market.html', context)


def detail_market(request, slug):
    boutique = get_object_or_404(Boutique, slug=slug)
    query = request.GET.get('q')
    produits = boutique.produits.all()
    
    if query:
        produits = produits.filter(nom__icontains=query)
        
    context={
        'boutique':boutique,
        'produits':produits
    }
    return render(request, 'mplace/place/detail_market.html', context)
def contact(request):
    return render(request, 'mplace/body/contact.html')