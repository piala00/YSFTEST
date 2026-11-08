"""Dé-duplication des menus (#72 étape A) : les commandes globales du Fichier sont définies une fois.

On vérifie que le bloc commun (Autorisations, Journal des événements, Sauvegarde et restauration)
reste présent et correct dans chaque module qui l'utilise, après extraction dans un seul helper.
"""
from django.test import SimpleTestCase

from apps.core import navigation as nav

COMMUNES = ("fichier.autorisations", "fichier.journal_evenements", "fichier.sauvegarde")


class EntreesCommunesTests(SimpleTestCase):
    def test_helper_rend_les_trois_commandes_globales_du_module(self):
        entrees = nav.entrees_communes_fichier("transport")
        codes = [e.code for e in entrees]
        self.assertEqual(codes, list(COMMUNES))
        # Les URL sont bien préfixées par le module demandé.
        self.assertEqual(entrees[0].url, "transport:autorisations")
        self.assertEqual(entrees[2].url, "transport:sauvegarde")

    def _onglet_fichier(self, module):
        return next(o for o in module.onglets if o.code == "fichier")

    def test_commercial_fichier_contient_le_bloc_commun_une_seule_fois(self):
        fichier = self._onglet_fichier(nav.GESTION_COMMERCIALE)
        codes = [e.code for e in fichier.elements]
        for code in COMMUNES:
            self.assertEqual(codes.count(code), 1, f"{code} doit apparaître une seule fois")
        # URL correctement rattachées au module commercial.
        sauvegarde = next(e for e in fichier.elements if e.code == "fichier.sauvegarde")
        self.assertEqual(sauvegarde.url, "commercial:sauvegarde")

    def test_modules_generiques_exposent_le_bloc_commun(self):
        # Les modules qui s'appuient sur menu_fichier() doivent tous porter le bloc commun.
        for module in nav.MODULES:
            fichier = self._onglet_fichier(module)
            codes = {e.code for e in fichier.elements}
            if "fichier.sauvegarde" in codes:   # commercial + modules génériques
                for code in COMMUNES:
                    self.assertIn(code, codes, f"{module.code} doit exposer {code}")
