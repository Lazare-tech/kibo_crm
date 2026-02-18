from django import forms

class DynamicForm(forms.Form):
    def __init__(self, questions, *args, **kwargs):
        super(DynamicForm, self).__init__(*args, **kwargs)
        for q in questions:
            # On génère un champ différent selon le type choisi par Laz
            if q.field_type == 'text':
                self.fields[f'question_{q.id}'] = forms.CharField(label=q.label, required=q.required)
            elif q.field_type == 'paragraph':
                self.fields[f'question_{q.id}'] = forms.CharField(label=q.label, widget=forms.Textarea, required=q.required)
            elif q.field_type == 'number':
                self.fields[f'question_{q.id}'] = forms.IntegerField(label=q.label, required=q.required)
            elif q.field_type == 'email':
                self.fields[f'question_{q.id}'] = forms.EmailField(label=q.label, required=q.required)
###
from django import forms
from django.forms import inlineformset_factory
from .models import Form, Question

class FormCreationForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = ['title', 'description']

# Ce formset permet d'ajouter dynamiquement des questions au formulaire
QuestionFormSet = inlineformset_factory(
    Form, Question, 
    fields=['label', 'field_type', 'required', 'order'],
    extra=3,  # Propose 3 champs vides par défaut
    can_delete=True
)