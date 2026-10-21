"""Fichier › Sauvegarde et restauration."""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TransactionTestCase
from django.urls import reverse

from apps.commercial.models import Tiers
from apps.core import sauvegarde
from apps.core.models import JournalEvenement


class SauvegardeTests(TransactionTestCase):
    def setUp(self):
        call_command("init_erp", verbosity=0)
        self.admin = get_user_model().objects.create_superuser("chef", "", "Chef-2026")
        Tiers.objects.create(code="CSAUVE", nom="Client sauvegardé")

    def test_sauvegarde_puis_restauration(self):
        self.client.force_login(self.admin)
        url = reverse("commercial:sauvegarde")
        reponse = self.client.post(url, {"action": "sauvegarder"})
        self.assertEqual(reponse.status_code, 200)
        self.assertIn("attachment", reponse["Content-Disposition"])
        contenu = reponse.content
        Tiers.objects.create(code="CAPRES", nom="Créé après la sauvegarde")
        Tiers.objects.filter(code="CSAUVE").delete()
        evenements_avant = JournalEvenement.objects.count()

        fichier = SimpleUploadedFile("sauvegarde.json", contenu, content_type="application/json")
        self.client.post(url, {"action": "restaurer", "confirmation": "RESTAURER", "fichier": fichier})
        self.assertTrue(Tiers.objects.filter(code="CSAUVE").exists())
        self.assertFalse(Tiers.objects.filter(code="CAPRES").exists())
        self.assertTrue(get_user_model().objects.filter(username="chef", is_superuser=True).exists())
        # Le journal restauré n'est pas pollué par le rechargement (seul l'événement « Restauration » s'ajoute)
        self.assertTrue(JournalEvenement.objects.filter(action="RESTAURATION").exists())
        self.assertLess(JournalEvenement.objects.count(), evenements_avant)

    def test_fichier_refuse_sans_rien_modifier(self):
        for contenu in (b"pas du json", b'[{"model": "core.societe"}]'):
            with self.assertRaises(ValueError):
                sauvegarde.restaurer(contenu.decode())
        self.assertTrue(Tiers.objects.filter(code="CSAUVE").exists())

    def test_confirmation_et_droits(self):
        vendeur = get_user_model().objects.create_user("vendeur", "", "x")
        self.client.force_login(vendeur)
        self.assertEqual(self.client.get(reverse("comptabilite:sauvegarde")).status_code, 403)
        self.client.force_login(self.admin)
        fichier = SimpleUploadedFile("s.json", sauvegarde.sauvegarder().encode(), content_type="application/json")
        Tiers.objects.create(code="CRESTE", nom="Reste")
        self.client.post(reverse("comptabilite:sauvegarde"), {"action": "restaurer", "confirmation": "oui", "fichier": fichier})
        self.assertTrue(Tiers.objects.filter(code="CRESTE").exists())          # sans « RESTAURER », rien ne change
