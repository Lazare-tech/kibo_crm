from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.

class Lead(models.Model):
    # Les différents états d'un prospect
    STATUS_CHOICES = (
        ('nouveau', 'Nouveau'),
        ('contacte', 'Contacté'),
        ('en_cours', 'En cours'),
        ('gagne', 'Gagné'),
        ('perdu', 'Perdu'),
    )

    # D'où vient le prospect ?
    SOURCE_CHOICES = (
        ('google', 'Google'),
        ('facebook', 'Facebook'),
        ('appel', 'Appel direct'),
        ('site_web', 'Site Web'),
    )

    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(max_length=255)
    phone_number = models.CharField(max_length=20, verbose_name="Téléphone")
    description = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='nouveau')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='site_web')
    
    # L'agent commercial responsable du lead
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Prospect"
        verbose_name_plural = "Prospects"
####
class Note(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) 
    text = models.TextField(verbose_name="Commentaire")
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note pour {self.lead.last_name} le {self.date_added.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        ordering = ['-date_added'] # Les plus récentes en premier
        
    ##
class Deal(models.Model):
    STAGES = (
        ('qualification', 'Qualification'),
        ('proposition', 'Proposition envoyée'),
        ('negociation', 'Négociation'),
        ('gagne', 'Gagné (Fermé)'),
        ('perdu', 'Perdu (Fermé)'),
    )

    name = models.CharField(max_length=200, verbose_name="Nom de l'opportunité")
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="deals")
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Montant estimé (FCFA)")
    stage = models.CharField(max_length=20, choices=STAGES, default='qualification')
    expected_close_date = models.DateField(verbose_name="Date de clôture prévue")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.amount} FCFA)"

    class Meta:
        ordering = ['-expected_close_date']
####
class Task(models.Model):
    PRIORITY_CHOICES = (
        ('basse', 'Basse'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
    )

    title = models.CharField(max_length=200, verbose_name="Tâche à faire")
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="tasks")
    due_date = models.DateField(verbose_name="Date d'échéance")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='moyenne')
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.lead.last_name}"
    
#####
class Client(models.Model):
    lead = models.OneToOneField(Lead, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100,verbose_name="Prénom")
    last_name = models.CharField(max_length=100,verbose_name="Nom")
    email = models.EmailField(verbose_name="Email")
    phone_number = models.CharField(max_length=20,verbose_name="Téléphone")
    address = models.TextField(blank=True, null=True,verbose_name="Adresse")
    is_active = models.BooleanField(default=True)
    date_converted = models.DateTimeField(auto_now_add=True,verbose_name="Date de conversion")

    def __str__(self):
        return f"CLIENT: {self.first_name} {self.last_name}"
####

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('en_attente', 'En attente'),
        ('payee', 'Payée'),
        ('annulee', 'Annulée'),
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="invoices")
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    date_issued = models.DateField(auto_now_add=True)
    due_date = models.DateField()

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Génère un numéro unique type KIBO-2026-XXXX
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Facture {self.invoice_number} - {self.client.last_name}"