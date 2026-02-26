
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
import csv
import openpyxl
from .models import Form, Submission
# Create your views here.
from django.urls import reverse
from django.core.paginator import Paginator
from .models import Form, Submission
# from .forms import DynamicForm
from django.shortcuts import render, get_object_or_404, redirect

# from .forms import FormCreationForm, QuestionFormSet
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# ###
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

# @csrf_exempt
# def google_form_webhook(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             # On récupère le slug que la bibliothèque a mis dans "_slug"
#             slug = data.get('_slug') 
            
#             form_obj = get_object_or_404(Form, slug=slug)
            
#             # On nettoie les données pour ne pas enregistrer le slug dans les réponses
#             answers = {k: v for k, v in data.items() if not k.startswith('_')}
            
#             # Enregistrement
#             Submission.objects.create(
#                 form=form_obj,
#                 answers_data=answers
#             )
#             return JsonResponse({'status': 'success'}, status=201)
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=400)
#     return JsonResponse({'status': 'method not allowed'}, status=405)
from django.utils.text import slugify

@csrf_exempt

def google_form_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            raw_title = data.get('_form_name', 'Formulaire Sans Nom').strip()
            clean_title = raw_title.replace(' (réponses)', '').strip()
            
            # 1. Création ou récupération du formulaire
            form_obj, created = Form.objects.get_or_create(
                title=clean_title,
                defaults={
                    'slug': slugify(clean_title),
                }
            )

            # 2. Nettoyage des réponses de Google (conversion des listes en valeurs simples)
            raw_answers = data.get('responses', {})
            clean_answers = {k: v[0] if isinstance(v, list) else v for k, v in raw_answers.items()}
            
            # 3. Enregistrement de la soumission
            Submission.objects.create(
                form=form_obj,
                answers_data=clean_answers
            )
            
            return JsonResponse({'status': 'success', 'created': created}, status=201)

        except Exception as e:
            print(f"Erreur Webhook : {str(e)}") 
            return JsonResponse({'error': str(e)}, status=400)
########################################################################################

###############3
def form_list(request):
    forms = Form.objects.all().order_by('title')
    context={
        "forms": forms
    }
    return render(request, 'kibo_forms/form_list.html', context)
#####
from django.utils import timezone

def form_dashboard(request, slug):
    form_obj = get_object_or_404(Form, slug=slug)
    
    # 1. RÉCUPÉRATION GLOBALE (Pour l'export et les stats réelles)
    submissions_queryset = form_obj.submissions.all().order_by('-submitted_at')
    
    # Calcul des stats réelles (avant filtrage de recherche)
    today = timezone.now().date()
    today_count = submissions_queryset.filter(submitted_at__date=today).count()

    # 2. LOGIQUE D'EXPORTATION (On utilise le QuerySet complet ici)
    export_format = request.GET.get('export')
    if export_format in ['csv', 'excel']:
        return handle_export(export_format, slug, submissions_queryset)

    # 3. LOGIQUE DE RECHERCHE (On crée une copie pour l'affichage)
    query = request.GET.get('search', '')
    display_list = submissions_queryset # Par défaut, on affiche tout
    
    if query:
        # Filtrage sur le JSON (Python side)
        display_list = [
            s for s in submissions_queryset 
            if any(query.lower() in str(v).lower() for v in s.answers_data.values())
        ]

    # 4. STATS & PAGINATION SUR LES DONNÉES DE L'ÉCRAN
    total_found = len(display_list) if isinstance(display_list, list) else display_list.count()
    paginator = Paginator(display_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    # 5. HEADERS ACTIFS (Sur les 50 premiers pour la performance)
    active_headers = []
    if total_found > 0:
        first_item = display_list[0] if isinstance(display_list, list) else display_list.first()
        for key in first_item.answers_data.keys():
            if not key.startswith('_'):
                # On vérifie si la colonne a de la donnée dans l'échantillon
                sample = display_list[:50]
                if any(s.answers_data.get(key) for s in sample):
                    active_headers.append(key)

    context = {
        'form': form_obj,
        'page_obj': page_obj,
        'headers': active_headers,
        'search_query': query,
        'total_found': total_found,
        'today_count': today_count, # Ajouté pour tes cartes de stats
    }

    # 6. RÉPONSE HTMX OU NORMALE
    if request.headers.get('HX-Request'):
        return render(request, 'kibo_forms/partials/submission_table.html', context)
    
    return render(request, 'kibo_forms/dashboard.html', context)
##
import csv
import openpyxl
from django.http import HttpResponse

def handle_export(fmt, slug, queryset):
    """Fonction utilitaire pour gérer l'exportation complète"""
    if fmt == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="export_{slug}.csv"'
        
        writer = csv.writer(response)
        if queryset.exists():
            # En-têtes basés sur la première soumission
            headers = ['Date'] + list(queryset.first().answers_data.keys())
            writer.writerow(headers)
            
            for sub in queryset:
                row = [sub.submitted_at.strftime("%d/%m/%Y %H:%M")]
                row += [sub.answers_data.get(k, "") for k in headers[1:]]
                writer.writerow(row)
        return response

    elif fmt == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Réponses KIBO"
        
        if queryset.exists():
            headers = ['Date'] + list(queryset.first().answers_data.keys())
            ws.append(headers)
            
            for sub in queryset:
                # On retire le fuseau horaire pour la compatibilité Excel
                row = [sub.submitted_at.replace(tzinfo=None)]
                row += [str(sub.answers_data.get(k, "")) for k in headers[1:]]
                ws.append(row)
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="export_{slug}.xlsx"'
        wb.save(response)
        return response

from django.db.models import Count, F
from django.shortcuts import render, get_object_or_404
from .models import Form

from django.db.models import Count, F
def form_stats_view(request, slug):
    form = get_object_or_404(Form, slug=slug)
    submissions = form.submissions.all()
    total = submissions.count()
    all_stats = []

    for header in form.headers:
        question_data = submissions.annotate(
            answer_value=F(f'answers_data__{header}')
        ).values('answer_value').annotate(
            count=Count('id')
        ).order_by('-count')

        num_unique = len(question_data)
        
        # --- LOGIQUE DE SÉPARATION STRICTE ---
        
        # 1. IDENTITÉ (Nom, Prénom, Email) -> Histogramme Vertical (Image 1)
        # On détecte si c'est du texte très varié (presque unique)
        if num_unique > (total * 0.8) and total > 2:
            display_type = 'bar_vertical'
            
        # 2. CASES À COCHER / CHOIX MULTIPLES -> Histogramme Horizontal (Image 2)
        # Google utilise l'horizontal dès que le texte est un peu long ou pour les domaines
        elif 5 < num_unique <= 20:
            display_type = 'bar'
            
        # 3. PETITS CHOIX (Oui/Non, Sexe) -> Diagramme Circulaire
        elif 2 <= num_unique <= 5:
            display_type = 'pie'
            
        # 4. PAR DÉFAUT -> Liste textuelle
        else:
            display_type = 'text'

        all_stats.append({
            'label': header,
            'data': list(question_data),
            'display_type': display_type
        })

    return render(request, 'kibo_forms/stats.html', {
        'form': form, 'total': total, 'all_stats': all_stats
    })