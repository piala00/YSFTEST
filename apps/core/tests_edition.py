"""Transport et Gestion commerciale sont deux logiciels distincts : dans le programme livré,
on ne doit jamais atteindre l'autre métier, même par URL directe (EditionMiddleware)."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Societe


@override_settings(ERP_LICENCE=True)
class SeparationEditionsTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("chef", "", "Chef-2026-ok")
        self.client.force_login(self.admin)

    def activite(self, valeur):
        s = Societe.get()
        s.activite = valeur
        s.save(update_fields=["activite"])

    def test_transport_bloque_la_gestion_commerciale(self):
        self.activite(Societe.ACTIVITE_TRANSPORT)
        # Un écran purement commercial renvoie au portail, jamais au logiciel commercial.
        r = self.client.get(reverse("commercial:accueil"))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse("core:portail"))
        # Les écrans communs et le Transport restent accessibles.
        self.assertEqual(self.client.get(reverse("comptabilite:societe")).status_code, 200)
        self.assertEqual(self.client.get(reverse("transport:accueil")).status_code, 200)

    def test_commerce_bloque_le_transport(self):
        self.activite(Societe.ACTIVITE_COMMERCE)
        r = self.client.get(reverse("transport:accueil"))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse("core:portail"))
        self.assertEqual(self.client.get(reverse("commercial:accueil")).status_code, 200)

    def test_mixte_laisse_tout_passer(self):
        self.activite(Societe.ACTIVITE_MIXTE)
        self.assertEqual(self.client.get(reverse("commercial:accueil")).status_code, 200)
        self.assertEqual(self.client.get(reverse("transport:accueil")).status_code, 200)

    @override_settings(ERP_LICENCE=False)
    def test_hors_programme_compile_rien_nest_bloque(self):
        self.activite(Societe.ACTIVITE_TRANSPORT)
        self.assertEqual(self.client.get(reverse("commercial:accueil")).status_code, 200)
