from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Categorie, Boutique, ProduitMarket

class MarketplaceTestCase(TestCase):
    def setUp(self):
        # 1. Création d'une catégorie
        self.categorie = Categorie.objects.create(nom="Électronique")

        # 2. Création d'une boutique
        self.boutique = Boutique.objects.create(
            nom="Global Tech Burkina",
            ville="Ouagadougou",
            description="Vente de matériel informatique"
        )

        # 3. Préparation d'une image factice pour le produit
        self.fake_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )

    def test_slug_generation(self):
        """Vérifie que les slugs sont générés automatiquement à la sauvegarde"""
        self.assertEqual(self.categorie.slug, "electronique")
        self.assertEqual(self.boutique.slug, "global-tech-burkina")

    def test_produit_creation(self):
        """Vérifie la création d'un produit et sa liaison avec la boutique"""
        produit = ProduitMarket.objects.create(
            boutique=self.boutique,
            categorie=self.categorie,
            nom="Laptop Kibo Pro",
            description="Un ordinateur puissant",
            prix=450000,
            image=self.fake_image
        )
        
        self.assertEqual(produit.boutique.nom, "Global Tech Burkina")
        self.assertEqual(produit.prix, 450000)
        self.assertEqual(str(produit), "Laptop Kibo Pro")

    def test_cascade_delete(self):
        """Vérifie que supprimer une boutique supprime aussi ses produits"""
        ProduitMarket.objects.create(
            boutique=self.boutique,
            categorie=self.categorie,
            nom="Smartphone X",
            description="Test cascade",
            prix=100000,
            image=self.fake_image
        )
        
        produit_count_before = ProduitMarket.objects.count()
        self.assertEqual(produit_count_before, 1)
        
        # Suppression de la boutique
        self.boutique.delete()
        
        # Le produit doit avoir disparu
        produit_count_after = ProduitMarket.objects.count()
        self.assertEqual(produit_count_after, 0)

    def test_categorie_set_null(self):
        """Vérifie que supprimer une catégorie ne supprime pas le produit (on_delete=models.SET_NULL)"""
        produit = ProduitMarket.objects.create(
            boutique=self.boutique,
            categorie=self.categorie,
            nom="Article Test",
            description="Test null",
            prix=5000,
            image=self.fake_image
        )
        
        self.categorie.delete()
        produit.refresh_from_db()
        
        self.assertIsNone(produit.categorie)
        self.assertEqual(produit.nom, "Article Test")