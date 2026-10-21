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
        for url, attendus in (("/commercial/", ["Factures clients non réglées", "Bon de livraison", "Derniers documents"]),
                              ("/comptabilite/", ["Trésorerie", "Saisie par pièce", "Dernières écritures"])):
            reponse = self.client.get(url)
            self.assertEqual(reponse.status_code, 200)
            for texte in attendus:
                self.assertContains(reponse, texte)
            contenu = reponse.content.decode()
            main = contenu[contenu.find("<main"):]
            self.assertNotIn("Calculette Sage", main)          # plus de recopie du menu Édition dans la page
            # La barre verticale présente les menus de travail, pas Fenêtre
            self.assertEqual(reponse.context["onglet_arbre"]["code"], "traitement")
