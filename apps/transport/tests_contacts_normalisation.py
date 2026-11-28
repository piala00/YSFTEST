"""Vérifications exécutables sans Django des coordonnées réellement utilisées au guichet."""
import unittest

from .contacts_normalisation import nom_normalise, telephone_normalise


class NormalisationTests(unittest.TestCase):
    def test_formats_camerounais_equivalents(self):
        for valeur in ("699000001", "+237 699 000 001", "00237 (699) 000-001", "237699000001"):
            with self.subTest(valeur=valeur):
                self.assertEqual(telephone_normalise(valeur), "+237699000001")

    def test_international_et_ambigu_sans_pays_invente(self):
        self.assertEqual(telephone_normalise("+33 6 12 34 56 78"), "+33612345678")
        self.assertEqual(telephone_normalise("0712345678"), "0712345678")

    def test_incomplets_et_textes_non_recherchables(self):
        for valeur in (None, "", "699", "inconnu", "699000001 poste 2", "++237699000001", "1" * 16):
            self.assertEqual(telephone_normalise(valeur), "")

    def test_nom_accents_espaces_et_apostrophe(self):
        self.assertEqual(nom_normalise("  Élodie  N’DÉMO "), "elodie n demo")
        self.assertEqual(nom_normalise(None), "")
