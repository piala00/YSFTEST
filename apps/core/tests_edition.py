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


from django.contrib.auth import get_user_model


class FumeeEditionTransportTests(TestCase):
    """Rendu réel en édition transport : aucune page atteignable ne doit casser sur une route de
    commerce pur démontée. (À lancer avec ERP_EDITION=transport pour charger l'URLconf transport.)"""

    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser("chef", "", "Chef-2026-ok"))

    def test_pages_transport_se_rendent_sans_route_commerce(self):
        from django.urls import reverse
        for nom in ("reporting:dashboard", "comptabilite:accueil", "comptabilite:ecritures",
                    "comptabilite:clients", "comptabilite:operations_caisse", "transport:accueil",
                    "billetterie:accueil", "colis:accueil", "garage:accueil"):
            with self.subTest(page=nom):
                self.assertEqual(self.client.get(reverse(nom)).status_code, 200)

    def test_aucun_lien_de_menu_du_transport_ne_casse(self):
        """Parcourt tous les liens de menu atteignables en édition transport : aucun ne doit renvoyer
        une erreur serveur (500), notamment sur une route de commerce pur démontée."""
        from django.urls import NoReverseMatch, reverse
        from apps.core import navigation as nav

        vus = set()

        def visiter(elements):
            for e in nav.selon_metier(elements, {"transport"}):
                url = str(e.url) if e.url else ""
                if url and ":" in url and url not in vus and not e.args:
                    vus.add(url)
                    try:
                        chemin = reverse(url)
                    except NoReverseMatch:
                        continue                       # lien paramétré (détail) : pas de cible sans argument
                    code = self.client.get(chemin).status_code
                    self.assertNotEqual(code, 500, f"{url} ({chemin}) a renvoyé 500")
                if e.enfants:
                    visiter(e.enfants)

        for m in nav.MODULES:
            if m.code in nav.modules_hors_edition():
                continue
            for onglet in m.onglets:
                visiter(onglet.elements)
        self.assertGreater(len(vus), 30)               # on a bien parcouru les menus
