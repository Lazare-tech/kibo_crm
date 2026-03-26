import os
import django
import random

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') # Remplace par le nom de ton projet
django.setup()

from mplace.models import Categorie, Boutique, ProduitMarket

def run_seed():
    print("--- Début du Seed JagoPoint ---")

    # 1. Création des Catégories
    categories_noms = ['Électronique', 'Moto', 'Habit', 'Alimentation', 'Beauté']
    categories = []
    for nom in categories_noms:
        cat, created = Categorie.objects.get_or_create(nom=nom)
        categories.append(cat)
        if created: print(f"Catégorie '{nom}' créée.")

    # 2. Création des Boutiques (Commerçants)
    villes = ['Ouagadougou', 'Bobo-Dioulasso', 'Koudougou', 'Banfora']
    boutiques_data = [
        {'nom': 'Global Tech Burkina', 'ville': 'Ouagadougou', 'desc': 'Le leader du high-tech au Faso.'},
        {'nom': 'Moto Plus Faso', 'ville': 'Bobo-Dioulasso', 'desc': 'Toutes les marques de motos et pièces.'},
        {'nom': 'Mode Faso Koudougou', 'ville': 'Koudougou', 'desc': 'Prêt-à-porter moderne et traditionnel.'},
        {'nom': 'Alimentation du Peuple', 'ville': 'Ouagadougou', 'desc': 'Produits frais et de qualité.'},
        {'nom': 'Espace Beauté Jago', 'ville': 'Banfora', 'desc': 'Cosmétiques et soins naturels.'},
    ]

    boutiques = []
    for data in boutiques_data:
        b, created = Boutique.objects.get_or_create(
            nom=data['nom'],
            defaults={'ville': data['ville'], 'description': data['desc']}
        )
        boutiques.append(b)
        if created: print(f"Boutique '{data['nom']}' créée à {data['ville']}.")

    # 3. Création des Produits
    produits_exemples = [
        ('iPhone 15 Pro', 850000, 'Électronique'),
        ('Ordinateur KiboBook', 450000, 'Électronique'),
        ('Moto Yamaha 125', 1200000, 'Moto'),
        ('Casque Moto Homologué', 25000, 'Moto'),
        ('Sneakers Urban Run', 35000, 'Habit'),
        ('Costume Slim Fit', 65000, 'Habit'),
        ('Sac de Riz 25kg', 18500, 'Alimentation'),
        ('Huile de Palme 5L', 6500, 'Alimentation'),
        ('Parfum Jago Night', 45000, 'Beauté'),
        ('Crème de Karité Bio', 3500, 'Beauté'),
    ]

    for nom, prix, cat_nom in produits_exemples:
        # On choisit une boutique au hasard
        boutique_choisie = random.choice(boutiques)
        # On récupère l'objet catégorie correspondant
        categorie_objet = next(c for c in categories if c.nom == cat_nom)
        
        ProduitMarket.objects.create(
            boutique=boutique_choisie,
            categorie=categorie_objet,
            nom=nom,
            prix=prix,
            description=f"Superbe {nom.lower()} disponible chez {boutique_choisie.nom}.",
            # Note : L'image sera vide ici, il faudra en ajouter une via l'admin 
            # ou mettre un chemin vers une image existante dans media/
        )
        print(f"Produit '{nom}' ajouté à {boutique_choisie.nom}.")

    print("--- Seed terminé avec succès ! ---")

if __name__ == '__main__':
    run_seed()