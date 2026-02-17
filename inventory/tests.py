from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Product, Supplier, SupplierOrder, OrderLine, Category, StockMovement

User = get_user_model()

class KiboInventoryTest(TestCase):
    
    def setUp(self):
        """Préparation de l'environnement de test"""
        # 1. Créer un utilisateur
        self.user = User.objects.create_user(username='laz_dev', password='password123')
        
        # 2. Créer une catégorie et un fournisseur
        self.cat = Category.objects.create(name="Réseau")
        self.supplier = Supplier.objects.create(name="Global Telecom", phone="+226000000")
        
        # 3. Créer un produit avec 20 unités en stock
        self.product = Product.objects.create(
            name="Routeur Cisco",
            sku="CISCO-X1",
            category=self.cat,
            quantity=20,
            purchase_price=50000,
            selling_price=75000
        )

    def test_order_total_calculation(self):
        """TEST : Vérifier que le montant total se calcule automatiquement"""
        order = SupplierOrder.objects.create(
            order_number="CMD-001",
            supplier=self.supplier,
            created_by=self.user
        )
        # Créer une ligne : 5 articles à 50 000 F
        OrderLine.objects.create(
            order=order,
            product=self.product,
            quantity_ordered=5,
            unit_cost=50000
        )
        
        # Le total doit être 250 000
        order.refresh_from_db()
        self.assertEqual(order.total_amount, 250000)

    def test_stock_reception_logic(self):
        """TEST : Vérifier que la réception augmente le stock physique"""
        order = SupplierOrder.objects.create(
            order_number="CMD-002",
            supplier=self.supplier,
            created_by=self.user
        )
        OrderLine.objects.create(
            order=order,
            product=self.product,
            quantity_ordered=10,
            quantity_received=5,
            unit_cost=50000
        )

        # Action : Passer en reçu
        order.status = 'recu'
        order.save()
        
        # --- CE QU'IL FAUT AJOUTER ---
        order.process_stock_reception() 
        # -----------------------------

        # Le stock initial était de 20. 20 + 5 reçu = 25.
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 25)
    def test_prevent_duplicate_stock_movement(self):
        """TEST : Sécurité contre le double ajout de stock"""
        order = SupplierOrder.objects.create(
            order_number="CMD-003",
            supplier=self.supplier,
            created_by=self.user,
            status='recu' # Directement reçu
        )
        OrderLine.objects.create(
            order=order,
            product=self.product,
            quantity_ordered=10,
            quantity_received=10,
            unit_cost=50000
        )
        order.process_stock_reception()
        #
        order.process_stock_reception()
        # On simule un deuxième enregistrement (sauvegarde accidentelle)
        order.save()

        # On vérifie qu'il n'y a qu'UN SEUL mouvement de stock créé pour cette commande
        movements_count = StockMovement.objects.filter(reason__icontains=order.order_number).count()
        self.assertEqual(movements_count, 1)