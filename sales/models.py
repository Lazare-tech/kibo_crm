from django.db import models
from leads.models import Client  # Import de ton app CRM
from inventory.models import Product  # Import de ton app Stock
import uuid

# Create your models here.

class Sale(models.Model):
    PAYMENT_STATUS = (
        ('en_attente', 'En attente'),
        ('partiel', 'Partiellement payé'),
        ('paye', 'Payé'),
    )

    sale_number = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="sales",verbose_name="Client")
    date = models.DateTimeField(auto_now_add=True,verbose_name="Date de vente")
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0,verbose_name="Montant total")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=0, default=0,verbose_name="Montant payé")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='en_attente')

    def save(self, *args, **kwargs):
        if not self.sale_number:
            self.sale_number = f"FAC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    def update_payment_status(self):
        """
        Recalcule le montant total payé et met à jour le statut de la vente.
        """
        from django.db.models import Sum
        
        # On fait la somme de tous les paiements liés à cette vente
        total_paid = self.payments.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # On met à jour les champs de la vente
        self.amount_paid = total_paid
        
        if self.amount_paid >= self.total_amount:
            self.status = 'paye'
        elif self.amount_paid > 0:
            self.status = 'partiel'
        else:
            self.status = 'en_attente'
            
        # On sauvegarde les modifications de la vente sans déclencher de boucle infinie
        self.save()
    ####
    # Dans models.py, sous la classe Sale
    @property
    def balance_due(self):
        # C'est ici que la magie de la déduction opère
        return self.total_amount - self.amount_paid
    #####
    def save(self, *args, **kwargs):
        if not self.sale_number:
            self.sale_number = f"FAC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    ###
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
class Payment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=0,verbose_name="Montant du paiement")
    date_payment = models.DateTimeField(auto_now_add=True,verbose_name="Date du paiement")
    payment_method = models.CharField(max_length=50, choices=[
        ('cash', 'Espèces'),
        ('orange_money', 'Orange Money'),
        ('moov_money', 'Moov Money'),
        ('virement', 'Virement')
    ], default='cash')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Après chaque paiement, on met à jour le montant total payé dans la vente
        self.sale.update_payment_status()

    def __str__(self):
        return f"Paiement de {self.amount} F pour {self.sale.sale_number}"