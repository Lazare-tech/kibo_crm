from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from inventory.models import Product, Category
from sales.models import Sale, SaleItem
from leads.models import Client

class SaleStockTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(first_name="Client Test")
        self.cat = Category.objects.create(name="Divers")
        self.product = Product.objects.create(
            name="Article Test",
            quantity=50, # Stock initial
            purchase_price=100,
            selling_price=200,
            category=self.cat
        )

    def test_vente_diminue_stock(self):
        """Vérifie que la création d'un SaleItem baisse le stock de Product"""
        sale = Sale.objects.create(client=self.client)
        
        # On vend 10 articles
        SaleItem.objects.create(
            sale=sale,
            product=self.product,
            quantity=10,
            unit_price=200
        )
        
        self.product.refresh_from_db()
        # 50 - 10 = 40
        self.assertEqual(self.product.quantity, 40)