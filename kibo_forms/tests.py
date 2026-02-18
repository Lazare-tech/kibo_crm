from django.test import TestCase
from .models import Form, Question, Submission
from django.urls import reverse
from django.contrib.auth.models import User

# Create your tests here.

class KiboFormsLogicTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="expert", password="123")
        self.form = Form.objects.create(title="Sondage", created_by=self.user)
        Question.objects.create(form=self.form, label="Nom", field_type="text")
        Question.objects.create(form=self.form, label="Age", field_type="number")

    def test_json_submission_integrity(self):
        """Vérifie que le stockage JSON conserve bien les types de données"""
        data = {
            "Nom": "Yelmani",
            "Age": 28
        }
        sub = Submission.objects.create(form=self.form, answers_data=data)
        
        # On recharge depuis la base pour vérifier le JSON
        sub.refresh_from_db()
        self.assertEqual(sub.answers_data["Nom"], "Yelmani")
        self.assertEqual(sub.answers_data["Age"], 28)
        self.assertIsInstance(sub.answers_data["Age"], int) # On vérifie que c'est bien un nombre
####
class KiboFormsIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="123")
        self.form = Form.objects.create(title="Contact", created_by=self.user)
        # On crée une question pour le test
        self.q1 = Question.objects.create(
            form=self.form, label="Votre Message", field_type="text"
        )

    def test_complete_submission_flow(self):
        """Vérifie que l'envoi du formulaire crée bien une soumission en base"""
        
        # 1. On récupère l'URL de notre formulaire (utilise le slug généré)
        url = reverse('kibo_forms:form_detail', kwargs={'slug': self.form.slug})
        
        # 2. On simule un message envoyé par un client
        payload = {
            f'question_{self.q1.id}': "Bonjour KIBO, je veux un devis !"
        }
        
        # 3. ACT : On envoie la requête POST
        response = self.client.post(url, data=payload)
        
        # 4. ASSERT : On vérifie que la redirection a eu lieu (merci/thanks)
        self.assertEqual(response.status_code, 200) # Ou 302 si tu as une redirection
        
        # 5. VERIFICATION FINALE : Est-ce que le JSON est correct en base ?
        submission = Submission.objects.filter(form=self.form).first()
        self.assertIsNotNone(submission)
        self.assertEqual(submission.answers_data["Votre Message"], "Bonjour KIBO, je veux un devis !")
    ##
    def test_share_link_generation(self):
        form = Form.objects.create(title="Test Link", created_by=self.user)
        # On vérifie que le slug existe (ex: '4A5B6C')
        self.assertIsNotNone(form.slug)
        
        # On simule la vue de partage
        url = reverse('kibo_forms:form_share_link', kwargs={'slug': form.slug})
        response = self.client.get(url)
        self.assertContains(response, form.slug)