from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SaleItem
from inventory.models import StockMovement

@receiver(post_save, sender=SaleItem)
def update_stock_on_sale(sender, instance, created, **kwargs):
    if created:
        # 1. On crée le mouvement de stock automatiquement
        StockMovement.objects.create(
            product=instance.product,
            quantity=instance.quantity,
            movement_type='sortie',
            reason=f"Vente automatique : {instance.sale.sale_number}"
        )
        
        # 2. On déduit physiquement la quantité du produit
        product = instance.product
        product.quantity -= instance.quantity
        product.save()