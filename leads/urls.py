
#
from django.urls import path

import leads.views 


app_name = 'leads'
urlpatterns = [
    path('', leads.views.dashboard, name='home'),

    path('create/', leads.views.lead_create, name='lead-create'), 
    path('update/<int:pk>/', leads.views.lead_update, name='lead-update'), # <int:pk> capture l'ID
    path('delete/<int:pk>/', leads.views.lead_delete, name='lead-delete'),
    path('prospect/<int:pk>/', leads.views.lead_detail, name='lead-detail'),
    path('pipeline/', leads.views.pipeline_view, name='pipeline'),
    path('task/<int:pk>/toggle/', leads.views.toggle_task, name='toggle-task'),
    ####
    path('create/<int:lead_pk>/deal/', leads.views.deal_create, name='deal-create'),
    path('deal/<int:pk>/update-stage/', leads.views.update_deal_stage, name='update-deal-stage'),
    # Conversion d'un lead en client
    path('clients/', leads.views.client_list, name='client-list'),
    path('convert/<int:pk>/', leads.views.convert_lead_to_client, name='convert-to-client'),
    # PDF pour une facture
    path('invoice/<int:pk>/pdf/', leads.views.render_invoice_pdf, name='invoice-pdf'),
    path('client/<int:client_pk>/invoice/create/', leads.views.create_invoice, name='create-invoice'),
    path('client-passage/', leads.views.quick_create_client, name='quick-create-client')


]
