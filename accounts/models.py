from django.db import models

from mplace.models import Boutique
from django.contrib.auth.models import User


# Create your models here.
class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Propriétaire / Gérant'),
        ('vendeur', 'Vendeur (Accès Sales)'),
        ('stock', 'Stockiste (Accès Inventory)'),
        ('commercial', 'Commercial (Accès Leads)'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    boutique = models.ForeignKey(Boutique, on_delete=models.CASCADE, related_name='employes')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='vendeur')

    def __str__(self):
        return f"{self.user.username} - {self.role} @ {self.boutique.nom}"