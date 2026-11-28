"""Sauvegarde chiffrée anti-vol : round-trip AES-GCM, mot de passe et détection d'altération."""
from django.test import TestCase

from apps.core import coffre_sauvegarde as cs


class CoffreSauvegardeTests(TestCase):
    def test_round_trip_rend_le_contenu_exact(self):
        texte = '[{"model":"_entete","format":"erp-ohada-sauvegarde"}]'
        octets = cs.chiffrer(texte, "Mot-de-passe-fictif-1")
        self.assertTrue(cs.est_coffre(octets))
        self.assertEqual(cs.dechiffrer(octets, "Mot-de-passe-fictif-1"), texte)

    def test_mot_de_passe_obligatoire_au_chiffrement(self):
        with self.assertRaises(ValueError):
            cs.chiffrer("x", "")

    def test_mauvais_mot_de_passe_refuse(self):
        octets = cs.chiffrer("secret", "bon-mot-de-passe")
        with self.assertRaises(ValueError):
            cs.dechiffrer(octets, "mauvais-mot-de-passe")

    def test_fichier_altere_refuse(self):
        octets = bytearray(cs.chiffrer("secret", "bon-mot-de-passe"))
        octets[-1] ^= 0x01  # un octet modifié → l'étiquette GCM ne correspond plus
        with self.assertRaises(ValueError):
            cs.dechiffrer(bytes(octets), "bon-mot-de-passe")

    def test_fichier_non_coffre_refuse(self):
        self.assertFalse(cs.est_coffre(b'{"model":"_entete"}'))
        with self.assertRaises(ValueError):
            cs.dechiffrer(b"ceci n'est pas un coffre", "x")

    def test_deux_sauvegardes_sont_differentes_sel_et_nonce_aleatoires(self):
        a = cs.chiffrer("meme-contenu", "meme-mot-de-passe")
        b = cs.chiffrer("meme-contenu", "meme-mot-de-passe")
        self.assertNotEqual(a, b)                       # sel + nonce aléatoires
        self.assertEqual(cs.dechiffrer(a, "meme-mot-de-passe"),
                         cs.dechiffrer(b, "meme-mot-de-passe"))
