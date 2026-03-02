from pyexpat.errors import messages
from django.forms import DecimalField
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction

from sales.models import Sale
from .forms import StockAdjustmentForm
from .models import Product, Category,Supplier,SupplierOrder
from .models import StockMovement
from django.db.models import  F, Count, ExpressionWrapper, DecimalField
from django.db.models import Q,Sum
from django.db import transaction
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.utils import timezone
from datetime import timedelta

from inventory import models
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
@login_required
@login_required
def all_stock_history(request):
    # 1. Préparation des dates pour les stats fixes
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    # 2. Initialisation du QuerySet (On le crée d'abord !)
    movements = StockMovement.objects.select_related('product', 'user').all().order_by('-date')

    # 3. Récupération des filtres depuis la requête GET
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search')

    # 4. Application des filtres dynamiques sur le QuerySet
    if start_date and end_date:
        movements = movements.filter(date__date__range=[start_date, end_date])
    elif start_date:
        movements = movements.filter(date__date__gte=start_date)
    
    if search_query:
        movements = movements.filter(product__name__icontains=search_query)

    # 5. Calcul des stats (On utilise un QuerySet séparé pour que les cartes restent fixes)
    all_outs = StockMovement.objects.filter(movement_type='sortie')
    stats = {
        'out_today': all_outs.filter(date__date=today).aggregate(Sum('quantity'))['quantity__sum'] or 0,
        'out_week': all_outs.filter(date__date__gte=start_of_week).aggregate(Sum('quantity'))['quantity__sum'] or 0,
        'out_month': all_outs.filter(date__date__gte=start_of_month).aggregate(Sum('quantity'))['quantity__sum'] or 0,
    }

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'movements': movements,
        'stats': stats
    }

    # 6. Logique HTMX : Si c'est une requête HTMX, on renvoie uniquement les lignes du tableau
    if request.headers.get('HX-Request'):
        return render(request, 'inventory/partials/history_table_rows.html', context)

    return render(request, 'inventory/all_stock_history.html', context)#####
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
##########################################################################################################
                                                #GESTION COMMANDES
##########################################################################################################
@login_required

def order_list(request):
    # Optimisation : select_related pour le fournisseur, created_by
    orders = SupplierOrder.objects.select_related('supplier', 'created_by').all().order_by('-date_order')
    
    # INDISPENSABLE pour le Modal
    suppliers = Supplier.objects.all().order_by('name')
    products = Product.objects.all().order_by('name')
    status = SupplierOrder.STATUS_CHOICES

    stats = {
        'total_pending': orders.filter(status='commande').count(),
        'total_waiting': orders.filter(status='en_attente').count(),
        'total_received': orders.filter(status='recu').count(),
    }
    
    return render(request, 'inventory/order_list.html', {
        'orders': orders,
        'suppliers': suppliers,  # Ajouté
        'products': products,    # Ajouté
        'stats': stats,
        'status':status,
        'now': timezone.now() 
    })
################
@login_required
@transaction.atomic
def receive_order(request, order_id):
    order = get_object_or_404(SupplierOrder, id=order_id, status='commande')
    
    # 1. Parcourir chaque ligne de la commande
    for line in order.lines.all():
        product = line.product
        
        # 2. Créer le mouvement de stock (Entrée)
        from .models import StockMovement
        StockMovement.objects.create(
            product=product,
            quantity=line.quantity,
            movement_type='entree',
            reason=f"Réception commande {order.order_number}",
            user=request.user
        )
        
        # 3. Mettre à jour le stock physique et le prix d'achat si besoin
        product.quantity += line.quantity
        product.purchase_price = line.unit_cost # On met à jour le prix d'achat avec le dernier prix connu
        product.save()
    
    # 4. Marquer la commande comme reçue
    order.status = 'recu'
    order.save()
    
    messages.success(request, f"La commande {order.order_number} a été intégrée au stock !")
    return redirect('inventory:order-detail', order_id=order.id)
####
@login_required
@transaction.atomic
def receive_order(request, order_id):
    order = get_object_or_404(SupplierOrder, id=order_id, status='commande')
    
    # On valide que tout ce qui a été commandé est bien reçu 
    # (ou on peut laisser Laz modifier les quantités reçues avant)
    for line in order.lines.all():
        if line.quantity_received > 0:
            # 1. Mouvement de stock
            StockMovement.objects.create(
                product=line.product,
                quantity=line.quantity_received,
                movement_type='entree',
                reason=f"Réception CMD {order.order_number}",
                user=request.user
            )
            # 2. Mise à jour physique
            line.product.quantity += line.quantity_received
            line.product.save()

    order.status = 'recu'
    order.save()
    
    messages.success(request, f"Commande {order.order_number} réceptionnée avec succès !")
    return redirect('inventory:order-list')
####
@login_required
def kibo_analytics(request):
    today = timezone.now()
    last_30_days = today - timedelta(days=30)

    # 1. ANALYSE FINANCIÈRE
    total_sales = Sale.objects.filter(date__gte=last_30_days).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_purchases = SupplierOrder.objects.filter(status='recu', date_order__gte=last_30_days).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # 2. ANALYSE DES STOCKS
    inventory_value = Product.objects.aggregate(
        total=Sum(F('quantity') * F('purchase_price'), output_field=DecimalField())
    )['total'] or 0
    
    low_stock_count = Product.objects.filter(quantity__lte=F('min_stock_level')).count()

    # 3. PERFORMANCE FOURNISSEURS
    orders_delayed = SupplierOrder.objects.filter(
        status='commande', 
        expected_date__lt=today.date()
    ).count()

    # 4. TOP PRODUITS (Basé sur les mouvements de sortie)
    top_products = Product.objects.annotate(
        total_sold=Sum('movements__quantity', filter=Q(movements__movement_type='sortie'))
    ).order_by('-total_sold')[:5]

    context = {
        'sales_value': total_sales,
        'purchases_value': total_purchases,
        'margin': total_sales - total_purchases,
        'inventory_value': inventory_value,
        'low_stock_count': low_stock_count,
        'orders_delayed': orders_delayed,
        'top_products': top_products,
        'now': today,
    }
    return render(request, 'inventory/analytics.html', context)
###
from django.shortcuts import redirect
from django.contrib import messages
from .models import SupplierOrder, OrderLine, Supplier, Product
from django.db import transaction
from django.utils.dateparse import parse_date

@transaction.atomic
def create_order(request):
    if request.method == "POST":
        supplier_id = request.POST.get('supplier')
        status = request.POST.get('status')  # Récupère la valeur du select
        expected_date_str = request.POST.get('expected_date')
        
        # Listes envoyées par le formulaire
        product_ids = request.POST.getlist('product[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price[]')

        if supplier_id and product_ids:
            try:
                # 1. Création de la commande parente
                order = SupplierOrder.objects.create(
                    supplier_id=supplier_id,
                    expected_date=parse_date(expected_date_str) if expected_date_str else None,
                    created_by=request.user,
                    status=status # Utilise le choix du modal
                )
                
                # 2. Création des lignes de commande
                for i in range(len(product_ids)):
                    if product_ids[i]: # On vérifie qu'un produit a été sélectionné
                        OrderLine.objects.create(
                            order=order,
                            product_id=product_ids[i],
                            quantity_ordered=quantities[i],
                            unit_cost=prices[i]
                        )
                
                messages.success(request, f"Commande {order.order_number} créée avec succès !")
            except Exception as e:
                messages.error(request, f"Erreur lors de la création : {str(e)}")
        
        return redirect('inventory:order-list')