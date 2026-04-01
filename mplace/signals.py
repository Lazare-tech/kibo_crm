from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Boutique
from accounts.models import Profile

@receiver(post_save, sender=Boutique)
def create_owner_profile(sender, instance, created, **kwargs):
    if created:
        # On crée le profil automatiquement pour l'admin de la boutique
        Profile.objects.get_or_create(
            user=instance.admin,
            boutique=instance,
            defaults={'role': 'admin'} # Le créateur est toujours Admin
        )