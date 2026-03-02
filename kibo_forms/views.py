
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

from django.db import transaction, IntegrityError
from django.utils.text import slugify
import logging
logger = logging.getLogger(__name__)


@csrf_exempt
def google_form_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        # On récupère le slug envoyé par KiboEngine via PropertiesService
        slug = data.get('_slug')
        
        if not slug:
            logger.error("Requête reçue sans _slug")
            return JsonResponse({'error': 'Le slug est manquant'}, status=400)

        # ── 1. Recherche du formulaire (Obligatoire pour les graphiques)
        # On utilise le slug que tu as configuré dans le menu KIBO ADMIN
        form_obj = get_object_or_404(Form, slug=slug)

        # ── 2. Nettoyage des données pour les Graphiques (Crucial)
        # La deuxième fonction extrayait proprement les réponses :
        # On retire les métadonnées (_slug, _submitted_at)
        # Et on transforme les listes Google ['réponse'] en chaînes 'réponse'
        raw_answers = {k: v for k, v in data.items() if not k.startswith('_')}
        
        clean_answers = {
            k: v[0] if isinstance(v, list) and len(v) > 0 else v
            for k, v in raw_answers.items()
            if k  # On ignore les clés vides pour ne pas casser les diagrammes
        }

        # ── 3. Enregistrement sécurisé
        try:
            with transaction.atomic():
                # On enregistre la soumission
                submission = Submission.objects.create(
                    form=form_obj,
                    answers_data=clean_answers
                )
                
            logger.info(f"Soumission #{submission.pk} enregistrée pour le slug: {slug}")

            # ── 4. Réponse JSON complète
            return JsonResponse({
                'status': 'success',
                'slug_used': slug,
                'submission_id': submission.pk,
                'message': 'Données prêtes pour les diagrammes'
            }, status=201)

        except IntegrityError as e:
            return JsonResponse({'error': 'Erreur d\'intégrité base de données'}, status=409)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        logger.exception(f"Erreur Webhook KiboEngine : {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
# def google_form_webhook(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             slug = data.get('_slug')
            
#             # Recherche du formulaire par le slug saisi dans le menu KIBO ADMIN
#             form_obj = get_object_or_404(Form, slug=slug)
            
#             # Nettoyage : on sépare les métadonnées des vraies réponses
#             # On retire '_slug' et '_submitted_at' pour ne garder que les questions
#             answers = {k: v for k, v in data.items() if not k.startswith('_')}
            
#             # Enregistrement dans la base de données
#             Submission.objects.create(
#                 form=form_obj,
#                 answers_data=answers
#             )
            
#             return JsonResponse({'status': 'success', 'slug_used': slug}, status=201)
#         except Exception as e:
#             print(f"Erreur KiboEngine : {str(e)}")
#             return JsonResponse({'error': str(e)}, status=400)
            
#     return JsonResponse({'status': 'method not allowed'}, status=405)
# def google_form_webhook(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

#     try:
#         data = json.loads(request.body)
#     except json.JSONDecodeError as e:
#         logger.error(f"JSON invalide reçu : {e}")
#         return JsonResponse({'error': 'JSON invalide'}, status=400)

#     # ── 1. Extraction des champs
#     g_title   = (data.get('form_title', '') or '').strip()
#     g_desc    = (data.get('form_description', '') or '').strip()
#     g_form_id = (data.get('form_id', '') or '').strip()
#     g_responses = data.get('responses', {})

#     # ── 2. Titre de fallback
#     if not g_title:
#         g_title = "Formulaire Sans Titre"

#     # ── 3. Génération du slug
#     # Priorité : form_id Google (stable) > slugify du titre
#     if g_form_id:
#         slug_value = slugify(g_form_id)
#     else:
#         slug_value = slugify(g_title)

#     if not slug_value:
#         slug_value = "formulaire-sans-titre"

#     logger.info(f"Webhook reçu — titre: '{g_title}' | slug: '{slug_value}'")

#     try:
#         with transaction.atomic():
#             form_obj, created = Form.objects.update_or_create(
#                 slug=slug_value,          # Clé de lookup stable
#                 defaults={
#                     'title':       g_title,
#                     'nom':         g_title,
#                     'description': g_desc or None,
#                 }
#             )

#         action = "créé" if created else "mis à jour"
#         logger.info(f"Formulaire '{g_title}' {action} (slug: {slug_value})")

#         # ── 4. Nettoyage des réponses (Google envoie toujours des listes)
#         clean_answers = {
#             k: v[0] if isinstance(v, list) and len(v) > 0 else v
#             for k, v in g_responses.items()
#             if k  # On ignore les clés vides
#         }

#         # ── 5. Enregistrement de la soumission (même si vide, on trace)
#         submission = None
#         if clean_answers:
#             submission = Submission.objects.create(
#                 form=form_obj,
#                 answers_data=clean_answers
#             )
#             logger.info(f"Soumission #{submission.pk} créée pour '{g_title}'")

#         return JsonResponse({
#             'status':          'success',
#             'form_slug':       form_obj.slug,
#             'form_title':      form_obj.title,
#             'form_created':    created,
#             'submission_id':   submission.pk if submission else None,
#         }, status=201)

#     except IntegrityError as e:
#         logger.error(f"Conflit DB (IntegrityError) : {e}")
#         return JsonResponse({'error': 'Conflit en base de données', 'detail': str(e)}, status=409)

#     except Exception as e:
#         logger.exception(f"Erreur inattendue webhook : {e}")
#         return JsonResponse({'error': 'Erreur interne', 'detail': str(e)}, status=500)
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
    submissions = Submission.objects.filter(form=form)
    total = submissions.count()
    
    processed_stats = {}

    for sub in submissions:
        for question, answer in sub.answers_data.items():
            if not answer or question.startswith('_'): continue
            
            if question not in processed_stats:
                processed_stats[question] = {"type": "pie", "answers": []}
            
            # On stocke toutes les réponses pour cette question
            processed_stats[question]["answers"].append(answer)
        
    all_stats = []
    for question, info in processed_stats.items():
        answers = info["answers"]
        
        # --- LOGIQUE DE DÉTECTION SENIOR ---
        
        # 1. CAS : CASES À COCHER (Listes) -> BAR
        if any(isinstance(a, list) for a in answers):
            display_type = 'bar'
            data_counts = {}
            for a in answers:
                for choice in (a if isinstance(a, list) else [a]):
                    data_counts[choice] = data_counts.get(choice, 0) + 1
            data = [{'answer_value': k, 'count': v} for k, v in data_counts.items()]

        else:
            # On calcule la longueur moyenne des réponses textuelles
            total_chars = sum(len(str(a)) for a in answers)
            avg_length = total_chars / len(answers) if answers else 0
            unique_count = len(set([str(a) for a in answers]))

            # 2. CAS : PARAGRAPHES (Textes longs > 50 chars)
            if avg_length > 50:
                display_type = 'paragraph'
                data = answers # Liste brute

            # 3. CAS : RÉPONSES COURTES (Noms, Emails)
            elif unique_count > (total * 0.7) and total > 2:
                display_type = 'text'
                data = answers # Liste brute

            # 4. CAS : CHOIX UNIQUES (Radio/Select) -> PIE
            else:
                display_type = 'pie'
                data_counts = {}
                for a in answers:
                    data_counts[a] = data_counts.get(a, 0) + 1
                data = [{'answer_value': k, 'count': v} for k, v in data_counts.items()]

        all_stats.append({
            'label': question,
            'display_type': display_type,
            'data': data
        })

    return render(request, 'kibo_forms/stats.html', {'all_stats': all_stats, 'form': form, 'total': total})