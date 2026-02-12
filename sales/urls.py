# sales/urls.py
from django.urls import path
import sales.views

app_name = 'sales'

urlpatterns = [
    path('pos/', sales.views.pos_interface, name='pos-interface'),
    path('add-to-cart/<int:product_id>/', sales.views.add_to_cart, name='add-to-cart'),
    path('validate/', sales.views.validate_sale, name='validate-sale'), # Ajoute cette ligne
    path('update-line/', sales.views.update_line_htmx, name='update-line'),
    path('history/', sales.views.sale_list, name='sale-list'),
    path('generate/<int:sale_id>/', sales.views.generate_invoice_pdf, name='generate-invoice')
]