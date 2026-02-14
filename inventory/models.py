from django.db import models
from django.conf import settings
# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, null=True,verbose_name="Description")

    def __claire__(self):
        return self.name

    class Meta:
        verbose_name = "Catégorie"

    def __str__(self):
        return self.name
    
class Product(models.Model):
    UNIT_CHOICES = (
        ('unite', 'Unité'),
        ('kg', 'Kilogramme'),
        ('litre', 'Litre'),
        ('paquet', 'Paquet'),
    )

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200, verbose_name="Désignation")
    sku = models.CharField(max_length=50, unique=True, verbose_name="Code Article / SKU")
    description = models.TextField(blank=True, null=True,verbose_name="Description")
    
    # Quantités
    quantity = models.IntegerField(default=0, verbose_name="Stock Actuel")
    min_stock_level = models.IntegerField(default=5, verbose_name="Seuil d'alerte")
    
    # Prix
    purchase_price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Prix d'achat")
    selling_price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Prix de vente")
    
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='unite')
    date_added = models.DateTimeField(auto_now_add=True,verbose_name="Date d'ajout")

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level

class StockMovement(models.Model):
    MOVEMENT_TYPES = (
        ('entree', 'Entrée (Achat/Retour)'),
        ('sortie', 'Sortie (Vente/Perte)'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Vendeur / Auteur"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="movements")
    quantity = models.IntegerField()
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES,verbose_name="Type de mouvement")
    reason = models.CharField(max_length=255, verbose_name="Raison", help_text="Ex:Vente client, Nouvel arrivage")
    date = models.DateTimeField(auto_now_add=True,verbose_name="Date")

    def __str__(self):
        return f"{self.movement_type} - {self.product.name} ({self.quantity})"