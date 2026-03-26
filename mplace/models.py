from django.db import models

# Create your models here.
from django.db import models
from django.utils.text import slugify

class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom

class Boutique(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ville = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='boutiques/logos/', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom

class ProduitMarket(models.Model):
    boutique = models.ForeignKey(Boutique, on_delete=models.CASCADE, related_name='produits')
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True)
    nom = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(max_digits=12, decimal_places=0)
    image = models.ImageField(upload_to='market/produits/')
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom