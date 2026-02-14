from datetime import timezone
from django.shortcuts import render, get_object_or_404,redirect
from inventory import models
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
    clients = Client.objects.all()
    print(
        "clients",clients
    )
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
@transaction.atomic
def validate_sale(request):
    if request.method == 'POST':
        # ... (tes récupérations de données restent les mêmes) ...
        client_id = request.POST.get('client_id')
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        prices = request.POST.getlist('prices[]')
        
        # Nettoyage
        amount_paid = float(request.POST.get('amount_paid', '0').replace('\xa0', '').replace(' ', '') or 0)
        total_amount = float(request.POST.get('total_amount', '0').replace('\xa0', '').replace(' ', '') or 0)

        try:
            # 1. Créer la vente
            sale = Sale.objects.create(
                client_id=client_id,
                total_amount=total_amount,
                amount_paid=0,
                status='en_attente'
            )

            # 2. Créer les lignes + Gérer le stock avec l'AUTEUR
            from inventory.models import StockMovement # Import local pour éviter les imports circulaires
            
            for p_id, qty, price in zip(product_ids, quantities, prices):
                product = Product.objects.get(id=p_id)
                qty_int = int(qty)
                clean_price = str(price).replace('\xa0', '').replace(' ', '').replace(',', '.')

                if product.quantity < qty_int:
                    raise ValueError(f"Stock insuffisant pour {product.name}")

                # Création de l'item de vente
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=qty_int,
                    unit_price=float(clean_price)
                )

                # CRUCIAL : On crée le mouvement de stock ICI avec request.user
                StockMovement.objects.create(
                    product=product,
                    quantity=qty_int,
                    movement_type='sortie',
                    reason=f"Vente {sale.sale_number}",
                    user=request.user  # <--- C'est ici qu'on enregistre le vendeur !
                )

                # Mise à jour physique du stock
                product.quantity -= qty_int
                product.save()

            # 3. Créer le paiement
            if amount_paid > 0:
                Payment.objects.create(
                    sale=sale,
                    amount=amount_paid,
                    payment_method='cash'
                )
            else:
                sale.update_payment_status()

            messages.success(request, f"Vente {sale.sale_number} validée par {request.user.username} !")
            return redirect('sales:sale-detail', sale_id=sale.id)

        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")
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
        try:
            # NETTOYAGE : on enlève les espaces normaux et les espaces insécables (\xa0)
            # On remplace aussi la virgule par un point au cas où
            clean_price = str(p).replace('\xa0', '').replace(' ', '').replace(',', '.')
            
            if clean_amount := clean_price:
                total_invoice += float(clean_amount) * int(q or 1)
        except (ValueError, TypeError):
            continue
    
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
@transaction.atomic
def validate_sale(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        
        # 1. Nettoyage strict du montant reçu au POS
        raw_paid = request.POST.get('amount_paid', '0').replace('\xa0', '').replace(' ', '').replace(',', '.')
        amount_received = float(raw_paid or 0)
        
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        prices = request.POST.getlist('prices[]')

        try:
            # A. Calcul du total de la facture
            total_invoice = 0
            for p, q in zip(prices, quantities):
                clean_p = str(p).replace('\xa0', '').replace(' ', '').replace(',', '.')
                total_invoice += float(clean_p) * int(q)

            # B. CRÉATION DE LA VENTE (On initialise TOUT à 0 et en attente)
            sale = Sale.objects.create(
                client_id=client_id,
                total_amount=total_invoice,
                amount_paid=0,        # On laisse le Payment remplir ça
                status='en_attente'   # On laisse le Payment remplir ça
            )

            # C. CRÉATION DES ARTICLES
            for p_id, qty, price in zip(product_ids, quantities, prices):
                clean_p = str(price).replace('\xa0', '').replace(' ', '').replace(',', '.')
                SaleItem.objects.create(
                    sale=sale,
                    product_id=p_id,
                    quantity=int(qty),
                    unit_price=float(clean_p)
                )

            # D. CRÉATION DU PREMIER PAIEMENT (C'est lui qui va tout calculer proprement)
            if amount_received > 0:
                Payment.objects.create(
                    sale=sale,
                    amount=amount_received,
                    payment_method='cash'
                )
            else:
                # Si 0 F, on force juste une mise à jour du statut
                sale.update_payment_status()

            messages.success(request, f"Vente {sale.sale_number} validée !")
            return redirect('sales:sale-list')

        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")
            return redirect('sales:pos-interface')
    
    return redirect('sales:pos-interface')
###
def update_payment_status(self):
    from django.db.models import Sum
    
    # 1. On force Django à recalculer la somme réelle en base de données
    # On utilise .all() pour s'assurer de prendre tous les objets liés
    total_paid = self.payments.all().aggregate(Sum('amount'))['amount__sum'] or 0
    
    # 2. On met à jour les champs de l'instance actuelle
    self.amount_paid = total_paid
    
    # 3. Logique de statut ultra-précise
    if self.amount_paid >= self.total_amount:
        self.status = 'paye'
    elif self.amount_paid > 0:
        self.status = 'partiel'
    else:
        self.status = 'en_attente'
    
    # 4. Éviter la boucle infinie : on utilise update() au lieu de save()
    # Cela met à jour la base de données directement sans relancer la méthode save() de Sale
    type(self).objects.filter(id=self.id).update(
        amount_paid=self.amount_paid,
        status=self.status
    )
###
@login_required
def debt_list(request):
    # On filtre les ventes non totalement payées
    debts = Sale.objects.exclude(status='paye').order_by('-date')
    
    # Calcul du total des créances dehors
    total_debt = sum(s.balance_due for s in debts)
    
    return render(request, 'sales/debt_list.html', {
        'debts': debts,
        'total_debt': total_debt
    })
####
from django.http import HttpResponse
from .models import Payment, Sale

@login_required
def add_payment(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        method = request.POST.get('payment_method')
        
        if amount:
            # Création du paiement (le signal/save du modèle mettra à jour la Sale)
            Payment.objects.create(
                sale=sale,
                amount=float(amount),
                payment_method=method
            )
            # On renvoie un script pour fermer le modal et rafraîchir la liste des créances
            return HttpResponse('<script>window.location.reload();</script>')
    context={
        'sale':sale
    }
    return render(request, 'sales/partials/add_payment_modal.html', context)
###
@login_required
def sale_detail(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    # On récupère tous les paiements liés à cette vente, du plus récent au plus ancien
    payments = sale.payments.all().order_by('-date_payment')
    context={
        'sale':sale,
        'payments':payments
    }
    return render(request, 'sales/sale_detail.html', context)
####
