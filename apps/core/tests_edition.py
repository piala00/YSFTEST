"""Transport et Gestion commerciale sont deux logiciels distincts : le logiciel livré (édition)
ne présente QUE les modules de son métier (composition, pas blocage)."""
from django.test import TestCase, override_settings

from .models import Societe
from .navigation import modules_proposes


class CompositionParEditionTests(TestCase):
    def codes(self):
        return {m.code for m in modules_proposes(Societe.get())}

    @override_settings(ERP_EDITION="transport")
    def test_le_transport_ne_contient_pas_la_gestion_commerciale(self):
        codes = self.codes()
        self.assertNotIn("commercial", codes)
        self.assertIn("transport", codes)
        self.assertIn("billetterie", codes)
        self.assertIn("garage", codes)
        self.assertIn("comptabilite", codes)      # les modules communs restent

    @override_settings(ERP_EDITION="commerce")
    def test_le_commerce_ne_contient_pas_le_transport(self):
        codes = self.codes()
        self.assertIn("commercial", codes)
        self.assertNotIn("transport", codes)
        self.assertNotIn("billetterie", codes)
        self.assertNotIn("garage", codes)
        self.assertIn("comptabilite", codes)

    @override_settings(ERP_EDITION="")
    def test_sans_edition_lactivite_decide(self):
        # Sans édition fixée (dév), c'est l'activité de la société qui compose.
        s = Societe.get()
        s.activite = Societe.ACTIVITE_MIXTE
        s.save(update_fields=["activite"])
        codes = self.codes()
        self.assertIn("commercial", codes)
        self.assertIn("transport", codes)
