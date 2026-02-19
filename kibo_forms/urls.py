from django.urls import path
import kibo_forms.views


app_name = 'kibo_forms'

urlpatterns = [
    # # C'est ici que 'form_detail' est défini
    path('list/', kibo_forms.views.form_list, name='form_list'),
    path('webhook/<slug:slug>/', kibo_forms.views.google_form_webhook, name='google_webhook'),
    path('dashboard/<slug:slug>/', kibo_forms.views.form_dashboard, name='form_dashboard'),
]