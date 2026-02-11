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