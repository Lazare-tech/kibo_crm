from django.urls import path
import kibo_forms.views


app_name = 'kibo_forms'

urlpatterns = [
    # C'est ici que 'form_detail' est défini
    path('f/<slug:slug>/', kibo_forms.views.form_detail, name='form_detail'),
    # Créer le formulaire
    path('create/', kibo_forms.views.create_kibo_form, name='create_kibo_form'),
    # Afficher le lien de partage (L'URL qui causait l'erreur)
    path('share/<slug:slug>/', kibo_forms.views.form_share_link, name='form_share_link'),
    path('add-question-field/', kibo_forms.views.add_question_field, name='add_question'),
]