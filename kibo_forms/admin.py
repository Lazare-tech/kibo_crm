from django.contrib import admin

import csv
import openpyxl
from django.urls import reverse
import json
from .models import Form, Submission

from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.http import HttpResponse
# admin.site.register(Submission)

############################################################################################
@admin.action(description="Exporter les réponses sélectionnées en CSV")
def export_submissions_csv(modeladmin, request, queryset):
    # On prépare la réponse HTTP pour un téléchargement de fichier
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="export_kibo_forms.csv"'
    
    writer = csv.writer(response)
    
    # On récupère toutes les clés (questions) du premier élément pour faire l'en-tête
    if queryset.exists():
        first_submission = queryset.first()
        headers = ['ID', 'Date de soumission'] + list(first_submission.answers_data.keys())
        writer.writerow(headers)
        
        # On remplit les lignes
        for obj in queryset:
            row = [obj.id, obj.submitted_at.strftime("%Y-%m-%d %H:%M")]
            for key in first_submission.answers_data.keys():
                # On récupère la réponse, si c'est une liste (cases à cocher), on la joint avec une virgule
                val = obj.answers_data.get(key, "")
                if isinstance(val, list):
                    val = ", ".join(map(str, val))
                row.append(val)
            writer.writerow(row)
            
    return response
####################################

@admin.action(description="Exporter en EXCEL (.xlsx)")
def export_submissions_excel(modeladmin, request, queryset):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Réponses KIBO"

    if queryset.exists():
        first_sub = queryset.first()
        headers = ['ID', 'Formulaire', 'Date'] + list(first_sub.answers_data.keys())
        ws.append(headers)

        # Style pour l'en-tête en gras
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)

        for obj in queryset:
            # On retire le fuseau horaire pour la compatibilité Excel
            date_str = obj.submitted_at.replace(tzinfo=None)
            row = [obj.id, obj.form.title, date_str]
            for key in first_sub.answers_data.keys():
                val = obj.answers_data.get(key, "")
                if isinstance(val, list): val = ", ".join(map(str, val))
                row.append(val)
            ws.append(row)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="export_kibo.xlsx"'
    wb.save(response)
    return response
####################################
@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('title', 'nom','description', 'slug')
    readonly_fields = ('webhook_url_display',)
    prepopulated_fields = {'slug': ('title',)}

    def webhook_url_display(self, obj):
        if obj.id:
            # Remplace par ton URL ngrok actuelle
            url = f"https://549a-102-23-40-244.ngrok-free.app/forms/webhook/{obj.slug}/"
            return mark_safe(f'<code style="background: #eee; padding: 5px; border: 1px solid #ccc;">{url}</code>')
        return "Enregistrez d'abord le formulaire pour voir l'URL"
    
    webhook_url_display.short_description = "URL du Webhook"

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    # On retire 'submitted_at' de list_display temporairement si l'erreur persiste
    list_display = ('id', 'form', 'submitted_at')
    list_filter = ('form', 'submitted_at')
    actions = [export_submissions_csv, export_submissions_excel]
    readonly_fields = ('answers_data_formatted', 'submitted_at')
    def answers_data_formatted(self, obj):
        if not obj.answers_data:
            return format_html('<span style="color: #999;">Aucune donnée.</span>')
            
        # 1. On prépare les styles CSS
        th_style = "padding: 10px; border: 1px solid #ddd; background: #f1f1f1; font-size: 11px; text-transform: uppercase; color: #666;"
        td_style = "padding: 10px; border: 1px solid #ddd; background: #fff; font-size: 13px; color: #333; min-width: 120px;"

        # 2. Construction du tableau
        html = ['<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse; text-align: left; border: 1px solid #ddd;">']
        
        # --- LIGNE DES EN-TÊTES (QUESTIONS) ---
        html.append('<thead><tr>')
        for key in obj.answers_data.keys():
            if not key.startswith('_'):
                html.append(f'<th style="{th_style}">{key}</th>')
        html.append('</tr></thead>')

        # --- LIGNE DES RÉPONSES ---
        html.append('<tbody><tr>')
        for key, value in obj.answers_data.items():
            if key.startswith('_'): 
                continue

            html.append(f'<td style="{td_style}">')
            
            # Gestion des fichiers
            if isinstance(value, list) and len(value) > 0 and str(value[0]).startswith("https://drive"):
                for v in value:
                    html.append(f'<a href="{v}" target="_blank" style="color: #264b5d; font-weight: bold; text-decoration: underline;">📄 Fichier</a><br>')
            
            # Gestion des listes (badges)
            elif isinstance(value, list):
                badges = "".join([f'<span style="background: #e1f5fe; color: #01579b; padding: 2px 5px; border-radius: 4px; font-size: 11px; margin-right: 3px; border: 1px solid #b3e5fc;">{v}</span>' for v in value])
                html.append(badges)
            
            # Texte normal
            else:
                html.append(str(value) if value else "—")
            
            html.append('</td>')
        
        html.append('</tr></tbody></table></div>')
        return format_html("".join(html))

    answers_data_formatted.short_description = "Aperçu horizontal des données"