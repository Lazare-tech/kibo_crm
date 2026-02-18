
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import uuid

class Form(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre du formulaire")
    description = models.TextField(blank=True,verbose_name="Description du formulaire")
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="Date de création")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Question(models.Model):
    FIELD_TYPES = (
        ('text', 'Texte court'),
        ('paragraph', 'Paragraphe (Long)'),
        ('number', 'Nombre'),
        ('email', 'Email'),
    )
    form = models.ForeignKey(Form, related_name='questions', on_delete=models.CASCADE)
    label = models.CharField(max_length=255, verbose_name="Libellé de la question")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text')
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

class Submission(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='submissions')
    # C'est ici que la magie opère : toutes les réponses sont dans ce dictionnaire
    answers_data = models.JSONField(default=dict) 
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Réponse au {self.form.title} le {self.submitted_at.strftime('%d/%m/%Y')}"