from django.urls import path
import inventory.views

app_name = 'inventory'

urlpatterns = [
    path('products/', inventory.views.product_list, name='product-list'),
    path('product/<int:pk>/get-card/', inventory.views.get_product_card, name='get-product-card'),
    path('product/<int:pk>/get-form/', inventory.views.get_stock_form, name='get-stock-form'),
    path('product/<int:pk>/adjust-htmx/', inventory.views.adjust_stock_htmx, name='adjust-stock-htmx'),
    path('product/<int:pk>/history/', inventory.views.stock_history, name='stock-history'),
    # --- Téléchargements & Exports ---
    path('product/<int:pk>/export-pdf/', inventory.views.export_stock_pdf, name='export-stock-pdf'),
]