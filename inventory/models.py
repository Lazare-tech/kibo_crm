import uuid
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
    quantity = models.IntegerField(verbose_name="Quantité")
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES,verbose_name="Type de mouvement")
    reason = models.CharField(max_length=255, verbose_name="Raison", help_text="Ex:Vente client, Nouvel arrivage")
    date = models.DateTimeField(auto_now_add=True,verbose_name="Date")

    def __str__(self):
        return f"{self.movement_type} - {self.product.name} ({self.quantity})"
###################################################################################################################
                                    #GESTION COMMANDE
###################################################################################################################

class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom du fournisseur")
    contact_name = models.CharField(max_length=100, blank=True, verbose_name="Nom du contact")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(blank=True,verbose_name="Email")
    address = models.TextField(blank=True,verbose_name="Adresse")

    def __str__(self):
        return self.name

class SupplierOrder(models.Model):
    STATUS_CHOICES = (
        ('en_attente', 'En attente'),
        ('commande', 'Commandé'),
        ('recu', 'Reçu (Terminé)'),
        ('annule', 'Annulé'),
    )

    order_number = models.CharField(max_length=50, unique=True, verbose_name="N° Commande")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="orders")
    date_order = models.DateTimeField(auto_now_add=True,verbose_name="Date de commande")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0,verbose_name="Montant total")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,verbose_name="Créé par")
    date_received = models.DateTimeField(null=True, blank=True, verbose_name="Date de réception effective")
    date_cancelled = models.DateTimeField(null=True, blank=True, verbose_name="Date d'annulation")
    #####
    def save(self, *args, **kwargs):
        # Logique pour capturer les dates lors du changement de statut
        if self.pk:
            old_status = SupplierOrder.objects.get(pk=self.pk).status
            if old_status != 'recu' and self.status == 'recu':
                from django.utils import timezone
                self.date_received = timezone.now()
            elif old_status != 'annule' and self.status == 'annule':
                from django.utils import timezone
                self.date_cancelled = timezone.now()
        # Si le numéro n'est pas encore défini (nouvelle commande)
        if not self.order_number:
            # Génère un code unique court (ex: CMD-8A2F)
            unique_id = uuid.uuid4().hex[:6].upper()
            self.order_number = f"CMD-{unique_id}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        # Utilise un fallback au cas où order_number serait quand même vide
        return f"{self.order_number or 'Sans Numéro'} - {self.supplier.name}"
 
class OrderLine(models.Model):
    order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE, related_name="lines",verbose_name="Commande")
    product = models.ForeignKey('Product', on_delete=models.CASCADE,verbose_name="Produit")
    quantity_ordered = models.IntegerField(verbose_name="Quantité commandée")
    quantity_received = models.IntegerField(default=0, verbose_name="Quantité reçue")
    unit_cost = models.DecimalField(max_digits=12, decimal_places=0,verbose_name="Prix d'achat unitaire")

    def __str__(self):
        return f"{self.product.name} x {self.quantity_ordered}"