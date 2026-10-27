"""Tests de non-régression proposés par GPT — risques de synchronisation.

Garanties corrigées par Claude après l'audit GPT lot 01 : un dépôt en échec est refait au passage suivant,
un lot n'en écrase jamais un autre au relais.
"""
import io
import tempfile
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.echanges import lots, synchro


class RepriseApresPanneTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)

    def test_echec_de_depot_ne_perd_pas_le_lot(self):
        """Après une panne réseau, la prochaine synchronisation doit retenter le lot."""
        lots.configurer_siege("SIEGE", "Siège")
        lots.ajouter_agence("DLA", "Douala")

        class Boite:
            def __init__(self):
                self.appels = 0
                self.depots = []

            def lister(self, code):
                return []

            def deposer(self, destination, nom, octets):
                self.appels += 1
                if self.appels == 1:
                    raise ConnectionError("panne réseau simulée")
                self.depots.append((destination, nom, octets))

        boite = Boite()
        premier = synchro.synchroniser(boite)
        self.assertTrue(premier.erreurs, "Le premier dépôt doit échouer")
        second = synchro.synchroniser(boite)
        self.assertFalse(second.erreurs)
        self.assertEqual(len(boite.depots), 1, "Le lot non livré doit être renvoyé")


class RelaisIdempotenceTests(TestCase):
    def setUp(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        reglages = override_settings(RELAIS_ACTIF=True, RELAIS_DOSSIER=dossier.name)
        reglages.enable()
        self.addCleanup(reglages.disable)
        self.jetons = {}
        for code in ("SIEGE", "DLA"):
            sortie = io.StringIO()
            call_command("relais_site", code=code, stdout=sortie)
            self.jetons[code] = sortie.getvalue().strip().splitlines()[-1]

    def deposer(self, corps):
        return self.client.post(
            "/relais/v1/boites/SIEGE/",
            data=corps,
            content_type="application/octet-stream",
            HTTP_AUTHORIZATION=f"Bearer {self.jetons['DLA']}",
            HTTP_X_NOM_LOT="ERP-LOT-DLA-vers-SIEGE-20261027-1000-1-5.erpx.chiffre",
        )

    def test_meme_nom_avec_contenu_different_refuse(self):
        self.assertEqual(self.deposer(b"contenu-original").status_code, 201)
        self.assertEqual(self.deposer(b"contenu-altere").status_code, 409)

    def test_meme_depot_rejoue_accepte(self):
        self.assertEqual(self.deposer(b"contenu").status_code, 201)
        self.assertEqual(self.deposer(b"contenu").status_code, 201)

    def test_taille_annoncee_trop_grande_refusee_sans_lecture(self):
        reponse = self.client.post("/relais/v1/boites/SIEGE/", data=b"x", content_type="application/octet-stream",
                                   HTTP_AUTHORIZATION=f"Bearer {self.jetons['DLA']}", CONTENT_LENGTH=str(61 * 1024 * 1024),
                                   HTTP_X_NOM_LOT="ERP-LOT-DLA-vers-SIEGE-20261027-1000-1-5.erpx.chiffre")
        self.assertEqual(reponse.status_code, 413)

    def test_lot_de_plusieurs_mega_octets(self):
        """Au-delà de la limite par défaut de Django (2,5 Mo) : lu en flux, accepté."""
        self.assertEqual(self.deposer(b"x" * (4 * 1024 * 1024)).status_code, 201)
