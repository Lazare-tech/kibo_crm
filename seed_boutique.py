import os
import django
import uuid
from django.utils import timezone

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') 
django.setup()

from django.contrib.auth.models import User
from mplace.models import Boutique, Categorie, ProduitMarket
from accounts.models import Profile
from inventory.models import Product
from leads.models import Lead, Client, Invoice
from sales.models import Sale

def run_seed():
    print("--- Début du seeding JagoPoint ---")

    # 1. CRÉATION DES UTILISATEURS (PROPRIÉTAIRES)
    boss_a, _ = User.objects.get_or_create(username='boss_a', email='boss_a@jago.bf')
    boss_a.set_password('pass123')
    boss_a.save()

    boss_b, _ = User.objects.get_or_create(username='boss_b', email='boss_b@jago.bf')
    boss_b.set_password('pass123')
    boss_b.save()

    # 2. CRÉATION DES BOUTIQUES
    b_moto, _ = Boutique.objects.get_or_create(
        admin=boss_a, 
        nom="Safi Motos", 
        ville="Bobo-Dioulasso", 
        is_active=True
    )
    
    b_friperie, _ = Boutique.objects.get_or_create(
        admin=boss_b, 
        nom="Sira Friperie", 
        ville="Ouagadougou", 
        is_active=True
    )

    # 3. CRÉATION DES PROFILS
    Profile.objects.get_or_create(user=boss_a, boutique=b_moto, role='admin')
    Profile.objects.get_or_create(user=boss_b, boutique=b_friperie, role='admin')

    # 4. CRÉATION DES CATÉGORIES (UNIFIÉES - SANS BOUTIQUE)
    # Note: On utilise 'nom' et pas 'name'
    cat_moto, _ = Categorie.objects.get_or_create(nom="Engins")
    cat_fripe, _ = Categorie.objects.get_or_create(nom="Vêtements")

    # 5. INVENTAIRE (ERP - PRIVÉ)
    p1_erp = Product.objects.create(
        boutique=b_moto, 
        category=cat_moto, 
        name="Sirius 110", 
        sku="MOTO-01", 
        quantity=10, 
        purchase_price=450000, 
        selling_price=550000
    )

    p2_erp = Product.objects.create(
        boutique=b_friperie, 
        category=cat_fripe, 
        name="Chemise XL", 
        sku="CH-01", 
        quantity=50, 
        purchase_price=2000, 
        selling_price=5000
    )

    # 6. PRODUITS MARKETPLACE (PUBLIC - POUR VOIR SUR L'ACCUEIL)
    # C'est ici que tu définis ce qui apparaît sur le site index.html
    ProduitMarket.objects.create(
        boutique=b_moto,
        categorie=cat_moto,
        nom="Moto Sirius 110 Neuve",
        description="Superbe moto pour circuler à Bobo-Dioulasso",
        prix=550000,
        # image=... (laisse vide ou gère le chemin si tu as une image de test)
    )

    ProduitMarket.objects.create(
        boutique=b_friperie,
        categorie=cat_fripe,
        nom="Chemise Homme Originale",
        description="Friperie de qualité venant de France",
        prix=5000,
    )

    # 7. CRM : LEADS ET CLIENTS (PRIVÉS)
    lead_a = Lead.objects.create(
        boutique=b_moto, 
        first_name="Issouf", 
        last_name="Traoré", 
        phone_number="70000001", 
        status='nouveau'
    )

    client_b = Client.objects.create(
        boutique=b_friperie, 
        first_name="Fatou", 
        last_name="Ouédraogo", 
        phone_number="76000002"
    )

    # 8. VENTES (PRIVÉES)
    sale = Sale.objects.create(
        boutique=b_friperie, 
        client=client_b, 
        total_amount=5000, 
        amount_paid=5000, 
        status='paye'
    )
    
    print("--- Seed terminé avec succès ! ---")
    print(f"Boutique A: {b_moto.nom} -> Connectez-vous avec boss_a / pass123")
    print(f"Boutique B: {b_friperie.nom} -> Connectez-vous avec boss_b / pass123")

if __name__ == '__main__':
    run_seed()