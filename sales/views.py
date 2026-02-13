from datetime import timezone
from django.shortcuts import render, get_object_or_404,redirect
from inventory.models import Product
from .models import Sale, SaleItem
from inventory.models import Category
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from leads.models  import Client
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils import timezone
from django.db.models import Sum
# Create your views here.


@login_required
def pos_interface(request):
    products = Product.objects.filter(quantity__gt=0) # On ne montre que ce qui est disponible
    categories = Category.objects.all()
    #
    clients = Client.objects.all().order_by('last_name')
    context={
        'products':products,
        'categories':categories,
        'clients':clients
    }
    return render(request, 'sales/pos_interface.html', context)

# Vue HTMX pour ajouter un produit au panier temporaire
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Logique de gestion du panier en session ou fragment HTML
    context={
        'product':product
    }
    return render(request, 'sales/partials/cart_item.html', context)
####
@login_required
def validate_sale(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        amount_paid = float(request.POST.get('amount_paid') or 0)
        total_amount = float(request.POST.get('total_amount') or 0)

        if not product_ids:
            messages.error(request, "Le panier est vide !")
            return redirect('sales:pos-interface')

        try:
            with transaction.atomic():
                # 1. Créer l'entête de la vente
                status = 'paye' if amount_paid >= total_amount else 'partiel'
                if amount_paid == 0: status = 'en_attente'
                
                sale = Sale.objects.create(
                    client_id=client_id,
                    total_amount=total_amount,
                    amount_paid=amount_paid,
                    status=status
                )

                # 2. Créer les lignes de vente (SaleItems)
                for p_id, qty in zip(product_ids, quantities):
                    product = Product.objects.get(id=p_id)
                    qty = int(qty)
                    
                    # Double vérification de sécurité pour le stock
                    if product.quantity < qty:
                        raise ValueError(f"Stock insuffisant pour {product.name}")

                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=qty,
                        unit_price=product.selling_price
                    )
                    # Note : Le signal que nous avons écrit plus haut s'occupe 
                    # automatiquement de créer le StockMovement et de baisser le stock.

                messages.success(request, f"Vente {sale.sale_number} validée avec succès !")
                # On pourrait rediriger vers la facture PDF ici
                return redirect('sales:pos-interface')

        except Exception as e:
            messages.error(request, f"Erreur lors de la vente : {str(e)}")
            return redirect('sales:pos-interface')
####

@login_required
def generate_invoice_pdf(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    template_path = 'sales/pdf/invoice.html'
    context = {'sale': sale}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Facture_{sale.sale_number}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Erreur PDF', status=500)
    return response
####
@login_required
def sale_list(request):
    today = timezone.now().date()
    sales = Sale.objects.all().order_by('-date')
    
    # Statistiques du jour
    stats = {
        'total_revenue': sales.filter(date__date=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'total_collected': sales.filter(date__date=today).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0,
        'sales_count': sales.filter(date__date=today).count(),
    }
    
    return render(request, 'sales/sale_list.html', {
        'sales': sales,
        'stats': stats
    })
####
from django.shortcuts import render
from django.http import HttpResponse

def calculate_totals(request):
    # On récupère les prix et quantités envoyés par le formulaire
    prices = request.GET.getlist('prices[]')
    quantities = request.GET.getlist('quantities[]')
    amount_received = float(request.GET.get('amount_paid') or 0)
    
    # Calcul du sous-total
    total_invoice = 0
    for p, q in zip(prices, quantities):
        total_invoice += float(p or 0) * int(q or 1)
    
    balance = amount_received - total_invoice
    
    context = {
        'total_invoice': total_invoice,
        'balance': balance,
        'balance_abs': abs(balance),
    }
    # On renvoie un fragment qui met à jour plusieurs zones (Out-of-Band)
    return render(request, 'sales/partials/pos_updates.html', context)
from django.shortcuts import render, get_object_or_404
from leads.models import Client
from inventory.models import Product
@login_required
def preview_sale(request):
    # 1. Récupération sécurisée du client
    client_id = request.POST.get('client_id')
    if not client_id:
        # On pourrait renvoyer une erreur HTMX ici si le client n'est pas choisi
        return HttpResponse("Veuillez choisir un client", status=400)
    
    client = get_object_or_404(Client, id=client_id)

    # 2. Récupération des listes
    product_ids = request.POST.getlist('product_ids[]')
    quantities = request.POST.getlist('quantities[]')
    prices = request.POST.getlist('prices[]')
    
    # 3. Nettoyage du montant reçu (Gestion des espaces et virgules)
    raw_amount_paid = request.POST.get('amount_paid', '0').replace('\xa0', '').replace(' ', '').replace(',', '.')
    try:
        amount_paid = float(raw_amount_paid or 0)
    except ValueError:
        amount_paid = 0

    items = []
    total_invoice = 0

    # 4. Boucle de calcul avec zip
    for p_id, qty, price in zip(product_ids, quantities, prices):
        if not p_id or not qty:
            continue
            
        try:
            product = Product.objects.get(id=p_id)
            # Nettoyage profond du prix envoyé par le formulaire
            clean_price = str(price).replace('\xa0', '').replace(' ', '').replace(',', '.')
            
            val_price = float(clean_price)
            val_qty = int(qty)
            line_total = val_price * val_qty
            
            total_invoice += line_total
            items.append({
                'product': product,
                'qty': val_qty,
                'price': val_price,
                'total': line_total
            })
        except (Product.DoesNotExist, ValueError, TypeError):
            continue

    # 5. Calcul de la balance finale
    balance = amount_paid - total_invoice

    context = {
        'client': client,
        'items': items,
        'total_invoice': total_invoice,
        'amount_paid': amount_paid,
        'balance': balance,
        'balance_abs': abs(balance), # Pour l'affichage sans le signe "-"
    }
    
    return render(request, 'sales/partials/modal_confirmation.html', context)
from django.shortcuts import redirect, get_object_or_404
from .models import Sale, SaleItem
from inventory.models import Product
@login_required

def validate_sale(request):
    if request.method == 'POST':
        # 1. Récupérer les infos de base
        client_id = request.POST.get('client_id')
        # Nettoyage du montant reçu (sécurité contre les espaces insécables)
        raw_paid = request.POST.get('amount_paid', '0').replace('\xa0', '').replace(' ', '')
        amount_paid = float(raw_paid or 0)
        
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        prices = request.POST.getlist('prices[]') # On récupère aussi les prix envoyés

        # 2. Utiliser une transaction atomique (Tout passe ou rien ne passe)
        with transaction.atomic():
            # A. Calculer le montant total réel
            total_invoice = 0
            sale_items_data = []
            
            for p_id, qty, price in zip(product_ids, quantities, prices):
                clean_price = str(price).replace('\xa0', '').replace(' ', '').replace(',', '.')
                line_total = float(clean_price) * int(qty)
                total_invoice += line_total
                
                # On prépare les données pour plus tard
                sale_items_data.append({
                    'product_id': p_id,
                    'quantity': int(qty),
                    'price': float(clean_price)
                })

            # B. Créer la Vente (On remplace l'Ellipsis par total_invoice)
            sale = Sale.objects.create(
                client_id=client_id,
                total_amount=total_invoice,
                amount_paid=amount_paid,
                # Le statut est géré automatiquement ou calculé ici
                status='paye' if amount_paid >= total_invoice else 'partiel'
            )

            # C. Créer les SaleItems (C'est ici que tes signaux de stock vont s'activer)
            for item in sale_items_data:
                SaleItem.objects.create(
                    sale=sale,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['price'] # Important de stocker le prix au moment de la vente
                )

        # 4. Rediriger vers la facture PDF
        return redirect('sales:sale-list')
    
    return redirect('sales:pos-interface')