from django import forms
from .models import Lead,Note,Deal,Task,Invoice

class LeadModelForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'description',
            'status',
            'source',
            'agent',
        )
##

class NoteModelForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ajouter un compte-rendu d\'appel, une remarque...'})
        }
##
class DealModelForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ('name', 'amount', 'stage', 'expected_close_date')
        widgets = {
            'expected_close_date': forms.DateInput(attrs={'type': 'date'}),
        }
###
class TaskModelForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('title', 'due_date', 'priority')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'title': forms.TextInput(attrs={'placeholder': 'Nouvelle tâche...', 'class': 'form-control form-control-sm'}),
            'priority': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }
####
class InvoiceModelForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ('amount', 'description', 'due_date', 'status')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'placeholder': 'Montant en FCFA', 'class': 'form-control'}),
            'description': forms.TextInput(attrs={'placeholder': 'Libellé de la prestation', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }