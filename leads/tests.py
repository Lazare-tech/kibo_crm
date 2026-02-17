from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Lead, Deal, Client
from datetime import date, timedelta

class CRMTestCase(TestCase):
    
    def setUp(self):
        """ÉTAPE 1 : ARRANGE (On prépare les données)"""
        self.user = User.objects.create_user(username='commercial1', password='password123')
        
        self.lead = Lead.objects.create(
            first_name="Jean",
            last_name="Dupont",
            email="jean@email.com",
            phone_number="70123456",
            status='nouveau',
            agent=self.user
        )

    def test_lead_creation(self):
        """Vérifie si un prospect est bien enregistré"""
        # ASSERT (Vérification)
        self.assertEqual(str(self.lead), "Jean Dupont")
        self.assertEqual(self.lead.status, 'nouveau')

    def test_deal_creation_for_lead(self):
        """ÉTAPE 2 & 3 : ACT & ASSERT (On crée une opportunité et on vérifie)"""
        deal = Deal.objects.create(
            name="Projet Solaire",
            lead=self.lead,
            amount=500000,
            stage='qualification',
            expected_close_date=date.today() + timedelta(days=30)
        )
        self.assertEqual(deal.lead.first_name, "Jean")
        self.assertEqual(self.lead.deals.count(), 1)

    def test_convert_lead_to_client(self):
        """Test crucial : La transformation d'un prospect en client"""
        # ACT : On crée manuellement un client à partir du lead
        client = Client.objects.create(
            lead=self.lead,
            first_name=self.lead.first_name,
            last_name=self.lead.last_name,
            email=self.lead.email,
            phone_number=self.lead.phone_number
        )
        
        # ASSERT
        self.assertTrue(Client.objects.filter(email="jean@email.com").exists())
        self.assertEqual(client.first_name, "Jean")
        # On vérifie la relation OneToOne
        self.assertEqual(self.lead.client.first_name, "Jean")

    def test_invoice_number_generation(self):
        """Vérifie que le numéro de facture se génère tout seul (ton UUID)"""
        client = Client.objects.create(
            first_name="Alizeta", last_name="Some", 
            email="ali@test.com", phone_number="60001161"
        )
        from .models import Invoice
        invoice = Invoice.objects.create(
            client=client,
            amount=150000,
            description="Installation Kit",
            due_date=date.today()
        )
        # Vérifie que le numéro commence bien par 'INV-' (Logique de ton save)
        self.assertTrue(invoice.invoice_number.startswith('INV-'))