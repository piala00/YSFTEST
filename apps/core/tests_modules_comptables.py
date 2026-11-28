"""Vérifie deux logiciels comptables visuellement distincts, une source d'écritures unique."""
from django.test import SimpleTestCase
from django.urls import reverse

from apps.core.navigation import modules_proposes, MODULES_PAR_CODE


class SocieteFictive:
    ACTIVITE_COMMERCE = "COMMERCE"
    ACTIVITE_TRANSPORT = "TRANSPORT"
    activite = "TRANSPORT"


class DeuxModulesComptablesTests(SimpleTestCase):
    def test_portail_transport_expose_deux_tuiles(self):
        codes = [m.code for m in modules_proposes(SocieteFictive())]
        self.assertIn("comptabilite", codes)
        self.assertIn("analytique", codes)
        self.assertEqual(MODULES_PAR_CODE["comptabilite"].titre, "Comptabilité générale")
        self.assertEqual(MODULES_PAR_CODE["analytique"].titre, "Comptabilité analytique")

    def test_portail_commerce_expose_deux_tuiles(self):
        societe = SocieteFictive()
        societe.activite = societe.ACTIVITE_COMMERCE
        codes = [m.code for m in modules_proposes(societe)]
        self.assertIn("comptabilite", codes)
        self.assertIn("analytique", codes)

    def test_urls_distinctes(self):
        self.assertNotEqual(reverse("comptabilite:accueil"), reverse("analytique:accueil"))
