from django.db import models
from leads.models import Client  # Import de ton app CRM
from inventory.models import Product  # Import de ton app Stock
import uuid

# Create your models here.

from django.db import models
from django.db.models import Sum  # Import indispensable pour le calcul
import uuid

class Sale(models.Model):
    PAYMENT_STATUS = (
        ('en_attente', 'En attente'),
        ('partiel', 'Partiellement payé'),
        ('paye', 'Payé'),
    )

    sale_number = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey('leads.Client', on_delete=models.CASCADE, related_name="sales", verbose_name="Client")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date de vente")
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Montant total")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Montant payé")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='en_attente')

    @property
    def balance_due(self):
        """Calcule dynamiquement le reste à payer."""
        return self.total_amount - self.amount_paid

    def update_payment_status(self):
        """Recalcule le cumul des paiements et met à jour le statut."""
        # Calcul de la somme de tous les objets Payment liés (via related_name="payments")
        result = self.payments.aggregate(Sum('amount'))
        total_paid = result['amount__sum'] or 0
        
        # Mise à jour du champ cumulatif
        self.amount_paid = total_paid
        
        # Logique de mise à jour du statut
        if self.amount_paid >= self.total_amount:
            self.status = 'paye'
        elif self.amount_paid > 0:
            self.status = 'partiel'
        else:
            self.status = 'en_attente'
            
        # Sauvegarde finale de la vente
        self.save()

    def save(self, *args, **kwargs):
        # Génération du numéro de facture unique s'il n'existe pas
        if not self.sale_number:
            self.sale_number = f"FAC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sale_number} - {self.client}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE,verbose_name="Produit")
    quantity = models.IntegerField(default=1,verbose_name="Quantité")
    unit_price = models.DecimalField(max_digits=12, decimal_places=0,verbose_name="Prix unitaire") # Fixé au moment de la vente
    total_line = models.DecimalField(max_digits=12, decimal_places=0, editable=False,verbose_name="Total ligne")

    def save(self, *args, **kwargs):
        self.total_line = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
###
from django.db import models, transaction

class Payment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Montant du paiement")
    date_payment = models.DateTimeField(auto_now_add=True, verbose_name="Date du paiement")
    payment_method = models.CharField(max_length=50, choices=[
        ('cash', 'Espèces'),
        ('orange_money', 'Orange Money'),
        ('moov_money', 'Moov Money'),
        ('virement', 'Virement')
    ], default='cash')

    def save(self, *args, **kwargs):
        # 1. On sauvegarde le paiement normalement
        super().save(*args, **kwargs)
        
        # 2. Sécurité KIBO : On attend que la transaction soit validée (committed)
        # pour demander à la vente de recalculer le total. 
        # Cela évite que update_payment_status ne "rate" le premier versement.
        transaction.on_commit(lambda: self.sale.update_payment_status())

    def __str__(self):
        return f"Paiement de {self.amount} F pour {self.sale.sale_number}"