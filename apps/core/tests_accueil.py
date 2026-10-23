from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase


class PageAccueilTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", demo=True, verbosity=0)

    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser("accueil", "", "x"))

    def test_accueil_raccourcis_et_indicateurs_sans_recopier_les_menus(self):
        for url, attendus in (("/commercial/", ["Factures clients non réglées", "Saisir un document de vente", "Accueil", "Tableau de bord"]),
                              ("/comptabilite/", ["Trésorerie", "Saisie par pièce", "Dernières écritures"])):
            reponse = self.client.get(url)
            self.assertEqual(reponse.status_code, 200)
            for texte in attendus:
                self.assertContains(reponse, texte)
            contenu = reponse.content.decode()
            main = contenu[contenu.find("<main"):]
            self.assertNotIn("Calculette", main)          # plus de recopie du menu Édition dans la page
            # La barre verticale présente les menus de travail, pas Fenêtre
            self.assertEqual(reponse.context["onglet_arbre"]["code"], "traitement")

    def test_bureau_et_fenetres_internes(self):
        """L'accueil est le bureau : les commandes s'y ouvrent dans des fenêtres internes (cadres du même site)."""
        reponse = self.client.get("/commercial/")
        self.assertContains(reponse, 'id="fenetres-mdi"')
        self.assertContains(reponse, "js/fenetres.js")
        self.assertEqual(reponse["X-Frame-Options"], "SAMEORIGIN")
        page = self.client.get("/commercial/clients/")                     # page ouverte dans une fenêtre
        self.assertNotContains(page, 'id="fenetres-mdi"')
        self.assertContains(page, "dans-fenetre")
        selection = self.client.get("/commercial/stock/mouvements/")      # boîte de dialogue titrée comme l'état
        self.assertContains(selection, "<title>Mouvements de stock")
