"""Exécuté aussi sous Windows : DPAPI réelle, sans serveur ni données de société."""
import unittest

from . import stockage as s


class StockageTests(unittest.TestCase):
    def test_aller_retour_et_aucun_code_en_clair(self):
        code = "ABCDEF-123456-GHIJKL-789012"
        valeur = s.sceller(code, "secret-essai", "poste-A")
        self.assertNotIn(code, valeur)
        self.assertEqual(s.ouvrir(valeur, "secret-essai", "poste-A"), code)
        self.assertNotEqual(valeur, s.sceller(code, "secret-essai", "poste-A"))

    def test_copie_vers_autre_poste_ou_autre_installation_refusee(self):
        valeur = s.sceller("code fictif", "secret-essai", "poste-A")
        for secret, machine in (("secret-essai", "poste-B"), ("autre-secret", "poste-A")):
            with self.assertRaises(ValueError):
                s.ouvrir(valeur, secret, machine)

    def test_contenu_tronque_ou_modifie_refuse(self):
        valeur = s.sceller("code fictif", "secret-essai", "poste-A")
        for modifie in ("en clair", s.PREFIXE + "!", valeur[:-5], valeur[:-12] + "AAAAAAAAAAAA"):
            with self.assertRaises(ValueError):
                s.ouvrir(modifie, "secret-essai", "poste-A")
