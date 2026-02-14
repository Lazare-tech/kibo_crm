from django.shortcuts import render, redirect, get_object_or_404
from .models import Lead,Deal,Task,Client
from inventory.models import Product
from .forms import LeadModelForm,NoteModelForm,DealModelForm,TaskModelForm,InvoiceModelForm
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.db.models import Q,Sum
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from datetime import date
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Invoice
# Create your views here.

@login_required
def dashboard(request):
    # Statistiques Financières (Invoices)
    total_encaisse = Invoice.objects.filter(status='payee').aggregate(Sum('amount'))['amount__sum'] or 0
    total_en_attente = Invoice.objects.filter(status='en_attente').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # On calcule la somme de tous les montants des deals
    total_pipeline = Deal.objects.filter(stage__in=['qualification', 'proposition', 'negociation']).aggregate(Sum('amount'))['amount__sum'] or 0
    # On récupère les 5 derniers prospects pour le dashboard
    stats_status = Lead.objects.values('status').annotate(total=Count('status'))
    labels = [dict(Lead.STATUS_CHOICES).get(s['status']) for s in stats_status]
    data = [s['total'] for s in stats_status]
    # On peut maintenant utiliser 'labels' et 'data' pour créer un graphique
    query = request.GET.get('q', '') #recuperer ce ki taper dans barre de recherche
    leads = Lead.objects.all().order_by('-date_added')#ajouter un slic[:5] pr ne afficher que 5 et dans ce cas la recherche vapa fonctionner
    if query:
        leads = leads.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query)
        )
    total_leads = Lead.objects.count()

    # Tâches urgentes (Aujourd'hui ou en retard et non terminées)
    urgent_tasks = Task.objects.filter(
        due_date__lte=date.today(),
        is_completed=False
    ).order_by('due_date')[:5] # On en prend 5 maximum pour le dashboard
    
    
    # --- DONNÉES INVENTAIRE ---
    total_products = Product.objects.count()
    # On récupère spécifiquement les produits en alerte
    low_stock_products = [p for p in Product.objects.all() if p.is_low_stock]
    low_stock_count = len(low_stock_products)
    
    context = {
        'leads': leads,
        'total_leads':Lead.objects.count(),
        'labels': labels,
        'data': data,
        'urgent_tasks': urgent_tasks,
        'total_pipeline': total_pipeline,
        'total_encaisse': total_encaisse,
        'total_en_attente': total_en_attente,
    }
    if not request.htmx:
        leads=leads[:5]
        
    if request.htmx:
        return render(request, 'leads/partials/lead_list.html', context)
    return render(request, 'leads/dashboard.html', context)
##
@login_required
def lead_create(request):
    if request.method == "POST":
        form = LeadModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("leads:home") # Vérifie que le nom 'dashboard' existe dans tes URLs
    else:
        form = LeadModelForm()
    
    print(f"DEBUG: Nombre de champs dans le formulaire : {len(form.fields)}")
    
    context = {
        "form": form
    }
    return render(request, "leads/lead_create.html", context)
##
@login_required
def lead_update(request, pk):
    # On récupère le prospect ou on affiche une erreur 404 s'il n'existe pas
    lead = get_object_or_404(Lead, pk=pk)
    
    if request.method == "POST":
        # On passe l'instance 'lead' pour que Django sache qu'on MODIFIE et non qu'on crée
        form = LeadModelForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            return redirect("leads:home")
    else:
        form = LeadModelForm(instance=lead)
    
    return render(request, "leads/lead_update.html", {
        "form": form,
        "lead": lead
    })
###
@login_required
@require_http_methods(['DELETE'])
def lead_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    lead.delete()
    # On renvoie une réponse vide pour que HTMX sache qu'il doit supprimer l'élément HTML
    return HttpResponse("")
##
@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    return render(request, "leads/lead_detail.html", {
        "lead": lead
    })
###
@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    notes = lead.notes.all() # Récupère toutes les notes liées
    tasks = lead.tasks.all().order_by('is_completed', 'due_date') # Tâches non finies en premier
    
    
    if request.method == "POST":
        # On vérifie si c'est un formulaire de note ou de tâche
        if 'task_submit' in request.POST:
            task_form = TaskModelForm(request.POST)
            if task_form.is_valid():
                task = task_form.save(commit=False)
                task.lead = lead
                task.save()
                return redirect('leads:lead-detail', pk=lead.pk)
        
    if request.method == "POST":
        form = NoteModelForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.lead = lead # On lie la note au prospect actuel
            note.author = request.user
            note.save()
            return redirect("leads:lead-detail", pk=lead.pk)
    else:
        task_form = TaskModelForm()
        form = NoteModelForm()

    return render(request, "leads/lead_detail.html", {
        "lead": lead,
        "notes": notes,
        "form": form,
        "tasks": tasks,
        "task_form": task_form,
    })
    
@login_required
def deal_create(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk)
    if request.method == "POST":
        form = DealModelForm(request.POST)
        if form.is_valid():
            deal = form.save(commit=False)
            deal.lead = lead
            deal.save()
            return redirect('leads:pipeline')
    else:
        form = DealModelForm()
    
    context={
        "form": form,
        "lead": lead
    }
    return render(request, "leads/deal_create.html", context)
###
@login_required
def pipeline_view(request):
    deals = Deal.objects.all()
    # On organise les deals par étape pour le template
    stages = [
        ('qualification', 'Qualification'),
        ('proposition', 'Proposition'),
        ('negociation', 'Négociation'),
        ('gagne', 'Gagné'),
    ]
    # On filtre pour ne prendre que les affaires non perdues (optionnel)
    total_pipeline_value = deals.exclude(stage='perdu').aggregate(Sum('amount'))['amount__sum'] or 0
    pipeline_data = []
    for stage_code, stage_name in stages:
        stage_deals = deals.filter(stage=stage_code)
        stage_total = stage_deals.aggregate(Sum('amount'))['amount__sum'] or 0
        pipeline_data.append({
            'code': stage_code,
            'name': stage_name,
            'deals': stage_deals,
            'total': stage_total
        })
    context={
        "pipeline": pipeline_data,
        "total_pipeline_value": total_pipeline_value
    }

    return render(request, "leads/pipeline.html", context)
##
@login_required
def toggle_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.is_completed = not task.is_completed
    task.save()
    context={
        "task": task
    }
    # On renvoie juste un petit bout de HTML (le nouveau statut de la tâche)
    return render(request, "leads/partials/task_item.html", context)
####
@login_required
def convert_lead_to_client(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    
    # On crée le client
    client, created = Client.objects.get_or_create(
        email=lead.email,
        defaults={
            'lead': lead,
            'first_name': lead.first_name,
            'last_name': lead.last_name,
            'phone_number': lead.phone_number,
        }
    )
    
    # On met à jour le statut du lead
    lead.status = 'gagne'
    lead.save()
    
    return redirect('leads:client-list') # On va créer cette liste
####
@login_required
def update_deal_stage(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    new_stage = request.POST.get('stage')
    
    if new_stage in dict(Deal.STAGES):
        deal.stage = new_stage
        deal.save()
        
    # On redirige vers la vue pipeline pour que HTMX rafraîchisse tout le tableau
    return pipeline_view(request)
###
@login_required
def client_list(request):
    clients = Client.objects.all().order_by('-date_converted')
    context={
        'clients':clients
    }
    return render(request, "leads/client_list.html", context)

###


def render_invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    template_path = 'leads/pdf/invoice_template.html'
    context = {'invoice': invoice, 'company_name': 'KIBO TECHNOLOGIES'}
    
    # Création de la réponse HTTP avec le type PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{invoice.invoice_number}.pdf"'
    
    # Rendu du template
    template = get_template(template_path)
    html = template.render(context)

    # Création du PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)
    return response
###
@login_required
def create_invoice(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    if request.method == "POST":
        form = InvoiceModelForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.client = client
            invoice.save()
            return redirect('leads:client-list')
    else:
        form = InvoiceModelForm()
    
    context={
        'form': form,
        'client': client
    }
    return render(request, "leads/invoice_create.html", context)
##
@login_required
def quick_create_client(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        
        client = Client.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone
        )
        
        # On renvoie une option HTML que HTMX va injecter et sélectionner
        return HttpResponse(f"""
            <option value="{client.id}" selected>{client.first_name} {client.last_name}</option>
            <script>
                document.getElementById('client-select').value = "{client.id}";
                bootstrap.Modal.getInstance(document.getElementById('modal-container').querySelector('.modal')).hide();
            </script>
        """)
    
    return render(request, 'leads/partials/quick_client_modal.html')