from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Form, Submission
from .forms import DynamicForm
from django.shortcuts import render, get_object_or_404, redirect
from .forms import FormCreationForm, QuestionFormSet

###
def form_detail(request, slug):
    form_obj = get_object_or_404(Form, slug=slug)
    questions = form_obj.questions.all()

    if request.method == 'POST':
        form = DynamicForm(questions, request.POST)
        if form.is_valid():
            # On prépare le dictionnaire JSON pour la base
            # Ex: {"Votre nom": "Lazare", "Votre âge": 25}
            answers = {}
            for q in questions:
                answers[q.label] = form.cleaned_data.get(f'question_{q.id}')

            # Sauvegarde Senior : tout dans une seule ligne !
            Submission.objects.create(form=form_obj, answers_data=answers)
            return render(request, 'kibo_forms/thanks.html')
    else:
        form = DynamicForm(questions)

    return render(request, 'kibo_forms/display_form.html', {'form': form, 'form_obj': form_obj})
#

def create_kibo_form(request):
    if request.method == 'POST':
        form = FormCreationForm(request.POST)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.created_by = request.user
            new_form.save() # Le slug est généré ici automatiquement
            
            formset = QuestionFormSet(request.POST, instance=new_form)
            if formset.is_valid():
                formset.save()
                return redirect('kibo_forms:form_share_link', slug=new_form.slug)
    else:
        form = FormCreationForm()
        formset = QuestionFormSet()

    return render(request, 'kibo_forms/create_form.html', {
        'form': form,
        'formset': formset
    })
def form_share_link(request, slug):
    # 1. On récupère l'URL complète pour le champ "Copier"
    full_url = request.build_absolute_uri(
        reverse('kibo_forms:form_detail', kwargs={'slug': slug})
    )
    
    # 2. On passe 'slug' au contexte pour le bouton "Voir mon formulaire" du template
    return render(request, 'kibo_forms/share.html', {
        'url': full_url,
        'slug': slug  # <--- NE PAS OUBLIER CETTE LIGNE
    })
def add_question_field(request):
    # On récupère le nombre actuel de formulaires pour indexer correctement le nouveau
    formset = QuestionFormSet()
    # On prend un formulaire vide (extra)
    form = formset.forms[0] 
    
    # On renvoie juste le fragment HTML du formulaire
    return render(request, 'kibo_forms/partials/question_form.html', {'form': form})