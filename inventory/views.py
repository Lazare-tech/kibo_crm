from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .forms import StockAdjustmentForm
from .models import Product, Category
from .models import StockMovement
from django.db.models import Sum, Q
from django.db import transaction
from xhtml2pdf import pisa
from django.template.loader import get_template
# Create your views here.

@login_required
def product_list(request):
    products = Product.objects.all().order_by('name')
    categories = Category.objects.all()
    #
    # Statistiques pour les graphiques
    # Calcul des sorties totales par produit
    for product in products:
        product.total_sales = product.movements.filter(movement_type='sortie').aggregate(Sum('quantity'))['quantity__sum'] or 0
    # Statistiques simples
    total_products = products.count()
    low_stock_count = sum(1 for p in products if p.is_low_stock)
    ##
    # Top 5 des produits les plus sortis
    top_products = sorted(products, key=lambda x: x.total_sales, reverse=True)[:5]
    top_labels = [p.name for p in top_products]
    top_data = [p.total_sales for p in top_products]
    ###
    context={
          'products': products,
        'categories': categories,
        'total_products': total_products,
        'low_stock_count': sum(1 for p in products if p.is_low_stock),
        'top_labels': top_labels,
        'top_data': top_data,
    
    }
    return render(request, 'inventory/product_list.html', context)
####

@login_required
def adjust_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            with transaction.atomic(): # Sécurité : tout passe ou rien ne passe
                movement = form.save(commit=False)
                movement.product = product
                
                # Mise à jour de la quantité réelle du produit
                if movement.movement_type == 'entree':
                    product.quantity += movement.quantity
                else:
                    product.quantity -= movement.quantity
                
                product.save()
                movement.save()
                
            return redirect('inventory:product-list')
    
    return render(request, 'inventory/adjust_stock.html', {
        'form': StockAdjustmentForm(),
        'product': product
    })
####
@login_required
def stock_history(request, pk):
    product = get_object_or_404(Product, pk=pk)
    movements = product.movements.all().order_by('-date')
    user=request.user
    ###
    context={
          'product': product,
        'movements': movements,
        'user': user
    }
    return render(request, 'inventory/stock_history.html', context)
#####
@login_required
def get_stock_form(request, pk):
    product = get_object_or_404(Product, pk=pk)
    ##
    context={
        'product': product
    }
    return render(request, 'inventory/partials/stock_form.html', context)

###
@login_required
def adjust_stock_htmx(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity'))
        m_type = request.POST.get('movement_type')
        reason = request.POST.get('reason')
        
        try:
            with transaction.atomic():
                # On valide d'abord la sortie
                if m_type == 'sortie' and product.quantity < qty:
                    return HttpResponse("⚠️ Stock insuffisant !", status=400)
                
                # Création du mouvement
                StockMovement.objects.create(
                    product=product,
                    quantity=qty,
                    movement_type=m_type,
                    reason=reason
                )
                
                # Mise à jour du produit
                if m_type == 'entree':
                    product.quantity += qty
                else:
                    product.quantity -= qty
                product.save()
                
        except Exception as e:
            return HttpResponse(f"Erreur : {str(e)}", status=500)
    context={
        'product': product
    }        
    return render(request, 'inventory/partials/product_card_inner.html', context)
###
@login_required
def get_product_card(request, pk):
    """
    Renvoie uniquement le fragment HTML d'une carte produit.
    Utilisé par HTMX pour l'annulation ou le rafraîchissement.
    """
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'inventory/partials/product_card_inner.html', {'product': product})
##
@login_required
def export_stock_pdf(request, pk):
    product = get_object_or_404(Product, pk=pk)
    movements = product.movements.all().order_by('-date')
    
    template_path = 'inventory/pdf/stock_report.html'
    context = {'product': product, 'movements': movements, 'user': request.user}
    
    # Création de la réponse PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Rapport_{product.sku}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)

    # Création du PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)
    return response