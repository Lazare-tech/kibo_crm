
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import uuid


#######################################################################################################################
from django.db import models

class Form(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True,verbose_name="Description du formulaire")
    nom=models.CharField(max_length=255, blank=True,null=True, verbose_name="Nom du formulaire")
    has_file_upload = models.BooleanField(default=False, verbose_name="Contient des fichiers ?",null=True)
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="Date de création")
    slug = models.SlugField(unique=True) # Utilisé dans l'URL du Webhook

class Submission(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='submissions',verbose_name="Formulaire associé")
    # C'est ici que tout est stocké (Textes, Nombres, Dates)
    answers_data = models.JSONField(default=dict) 
    submitted_at = models.DateTimeField(auto_now_add=True)
    file_links = models.TextField(blank=True, null=True, help_text="Liens vers les fichiers uploadés sur Google Drive")
    #####
    class Meta:
        verbose_name = "Réponse reçue"
        verbose_name_plural = "Réponses reçues"

    def __str__(self):
        # On affiche par exemple : "Réponse au formulaire Sondage (19/02/2026)"
        date_str = self.submitted_at.strftime("%d/%m/%Y %H:%M")
        return f"Réponse à {self.form.title} - {date_str}"