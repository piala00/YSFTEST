"""Contrats du menu Fichier global de l'ERP intégré."""
from unittest.mock import patch

from django.test import TestCase

from apps.core.navigation import MODULES, menu_fichier_global, structure_module


class MenuFichierGlobalTests(TestCase):
    def test_meme_menu_pour_tous_les_modules(self):
        with patch("apps.core.navigation._metier", return_value={"commerce", "transport"}):
            menus = [structure_module(module)[0][0] for module in MODULES]
        reference = [(item["code"], item["url"]) for item in menus[0]["elements"] if not item["separateur"]]
        for menu in menus:
            self.assertEqual(menu["code"], "fichier")
            self.assertEqual(reference, [(item["code"], item["url"]) for item in menu["elements"] if not item["separateur"]])

    def test_pas_de_doublons_et_commandes_non_realisees_grisees(self):
        menu = menu_fichier_global()
        codes = [element.code for element in menu.elements if not element.separateur]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertNotIn("fichier.poste", codes)
        for code in ("fichier.nouvelle_societe", "fichier.fermer_societe", "fichier.cloture_annuelle", "fichier.import_export"):
            element = next(element for element in menu.elements if element.code == code)
            self.assertFalse(element.url)
            self.assertFalse(element.action)
