from django.contrib import admin
import csv
import openpyxl
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.http import HttpResponse
from .models import Form, Submission

# --- 1. FONCTION DE RENDU UNIFIÉE (Pour les cartes) ---

def get_answers_html(obj):
    if not obj or not obj.answers_data:
        return format_html('<span style="color: #999;">Aucune donnée.</span>')

    container_id = f"grid-{obj.id}"
    styles = f"""
        <style>
            #{container_id} {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
                gap: 12px;
                background: #f1f3f4;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #dfe1e5;
                margin-top: 10px;
            }}
            #{container_id} .card {{
                background: white; border: 1px solid #dadce0;
                border-radius: 6px; padding: 12px;
                box-shadow: 0 1px 2px rgba(60,64,67,0.1);
            }}
            #{container_id} .label {{
                font-size: 10px; color: #70757a;
                text-transform: uppercase; font-weight: 700;
                margin-bottom: 6px; display: block;
            }}
            #{container_id} .val {{
                font-size: 13px; color: #202124;
                word-break: break-word; display: block;
            }}
        </style>
    """

    cards_html = ""
    # --- LA CORRECTION EST ICI ---
    for key, value in obj.answers_data.items():
        if key.startswith('_'): 
            continue
        
        # Formatage de la valeur (Fichiers, Badges ou Texte)
        if isinstance(value, list) and value and str(value[0]).startswith("http"):
            val_display = "<br>".join([f'<a href="{v}" target="_blank" style="color:#1a73e8;text-decoration:underline;">📄 Fichier</a>' for v in value])
        elif isinstance(value, list):
            val_display = "".join([f'<span style="background:#e8f0fe;color:#1a73e8;padding:2px 8px;border-radius:12px;font-size:11px;margin:2px;display:inline-block;border:1px solid #d2e3fc;">{v}</span>' for v in value])
        else:
            val_display = str(value) if value else "—"

        # On ajoute la carte à la chaîne finale (C'était cette ligne qui manquait)
        cards_html += format_html(
            '<div class="card"><span class="label">{}</span><span class="val">{}</span></div>',
            key, mark_safe(val_display)
        )

    # Assemblage final
    return mark_safe(f"{styles}<div id='{container_id}'>{cards_html}</div>")

# --- 2. ACTIONS D'EXPORTATION ---

@admin.action(description="Exporter en CSV")
def export_submissions_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="export_kibo_forms.csv"'
    writer = csv.writer(response)
    if queryset.exists():
        keys = set()
        for sub in queryset: keys.update(sub.answers_data.keys())
        headers = ['ID', 'Date'] + sorted([k for k in keys if not k.startswith('_')])
        writer.writerow(headers)
        for obj in queryset:
            row = [obj.id, obj.submitted_at.strftime("%Y-%m-%d %H:%M")]
            for key in headers[2:]:
                val = obj.answers_data.get(key, "")
                row.append(", ".join(map(str, val)) if isinstance(val, list) else val)
            writer.writerow(row)
    return response

@admin.action(description="Exporter en EXCEL (.xlsx)")
def export_submissions_excel(modeladmin, request, queryset):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Réponses KIBO"
    if queryset.exists():
        keys = set()
        for sub in queryset: keys.update(sub.answers_data.keys())
        headers = ['ID', 'Formulaire', 'Date'] + sorted([k for k in keys if not k.startswith('_')])
        ws.append(headers)
        for obj in queryset:
            date_str = obj.submitted_at.replace(tzinfo=None)
            row = [obj.id, obj.form.title, date_str]
            for key in headers[3:]:
                val = obj.answers_data.get(key, "")
                row.append(", ".join(map(str, val)) if isinstance(val, list) else val)
            ws.append(row)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="export_kibo.xlsx"'
    wb.save(response)
    return response

# --- 3. INLINE (Pour affichage dans la fiche Form) ---

class SubmissionInline(admin.StackedInline): 
    model = Submission
    extra = 0
    readonly_fields = ('submitted_at', 'render_answers')
    fields = ('submitted_at', 'render_answers')
    can_delete = True
    show_change_link = True

    def render_answers(self, obj):
        return get_answers_html(obj)
    render_answers.short_description = "Détail de la réponse"

# --- 4. ADMIN POUR LES FORMULAIRES ---

@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('title', 'nom', 'get_submission_count', 'slug')
    readonly_fields = ('webhook_url_display',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = [SubmissionInline]

    def get_submission_count(self, obj):
        count = obj.submissions.count()
        url = reverse('admin:kibo_forms_submission_changelist') + f'?form__id__exact={obj.id}'
        return format_html('<a href="{}" style="font-weight:bold; color:#4285F4;">📊 Voir {} réponses</a>', url, count)
    get_submission_count.short_description = "Total Réponses"

    def webhook_url_display(self, obj):
        if obj.id:
            url = f"https://549a-102-23-40-244.ngrok-free.app/forms/webhook/{obj.slug}/"
            return mark_safe(f'<code style="background: #e8f0fe; padding: 5px; border: 1px solid #1a73e8; border-radius:4px;">{url}</code>')
        return "Enregistrez d'abord pour voir l'URL"
    webhook_url_display.short_description = "URL du Webhook"

# --- 5. ADMIN POUR LES SOUMISSIONS ---

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'form', 'submitted_at')
    list_filter = ('form', 'submitted_at')
    actions = [export_submissions_csv, export_submissions_excel]
    readonly_fields = ('render_answers', 'submitted_at')

    def render_answers(self, obj):
        return get_answers_html(obj)
    render_answers.short_description = "Détail des réponses"