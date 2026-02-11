from django.contrib import admin
from .models import Lead,Note,Deal,Task,Invoice,Client
# Register your models here.


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'email', 'status', 'source', 'date_added')
    list_filter = ('status', 'source', 'agent')
    search_fields = ('first_name', 'last_name', 'email')
####
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'author', 'date_added', 'short_text')
    list_filter = ('date_added', 'author')
    search_fields = ('text', 'lead__last_name')
    readonly_fields = ('date_added',)

    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    short_text.short_description = "Extrait"


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('name', 'lead', 'amount', 'stage', 'expected_close_date')
    list_filter = ('stage', 'expected_close_date', 'created_at')
    list_editable = ('stage',) # Permet de changer l'étape sans entrer dans la fiche
    search_fields = ('name', 'lead__last_name')
    date_hierarchy = 'expected_close_date' # Barre de navigation temporelle


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'lead', 'due_date', 'priority', 'is_completed')
    list_filter = ('is_completed', 'priority', 'due_date')
    list_editable = ('is_completed', 'priority')
    search_fields = ('title', 'lead__last_name')
    actions = ['mark_as_completed']

    @admin.action(description="Marquer les tâches sélectionnées comme terminées")
    def mark_as_completed(self, request, queryset):
        queryset.update(is_completed=True)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone_number', 'date_converted', 'is_active')
    list_filter = ('is_active', 'date_converted')
    search_fields = ('first_name', 'last_name', 'email')
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = "Nom Complet"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'amount', 'status', 'date_issued', 'due_date')
    list_filter = ('status', 'date_issued')
    list_editable = ('status',)
    search_fields = ('invoice_number', 'client__last_name', 'description')
    readonly_fields = ('invoice_number', 'date_issued')
    
    # Ajout de couleurs pour le statut dans l'admin (Optionnel mais Pro)
    def get_status_display(self, obj):
        from django.utils.html import format_html
        colors = {
            'payee': 'green',
            'en_attente': 'orange',
            'annulee': 'red',
        }
        return format_html(
            '<span style="color: {}; fw-bold">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )