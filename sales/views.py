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
def update_line_htmx(request):
    try:
        qty = int(request.GET.get('qty', 1))
        price = float(request.GET.get('price', 0))
        total = qty * price
        
        # On renvoie un fragment HTML avec le display et le hidden
        html = f"""
            <span class="line-display">{total:,.0f}</span> F
            <input type="hidden" class="line-total-value" value="{total:.0f}">
        """
        # Note: on remplace les virgules par des espaces pour le display
        return HttpResponse(html.replace(',', ' '))
    except:
        return HttpResponse("0")
