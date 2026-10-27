"""Tests de non-régression proposés par GPT — risques de synchronisation.

Les tests marqués expectedFailure documentent des garanties non encore assurées.
Retirer expectedFailure uniquement après correction, puis vérifier la CI complète.
"""
import io
import tempfile
from unittest import expectedFailure, mock

from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.echanges import lots, synchro


class RepriseApresPanneTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)

    @expectedFailure
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

    @expectedFailure
    def test_meme_nom_avec_contenu_different_refuse(self):
        self.assertEqual(self.deposer(b"contenu-original").status_code, 201)
        self.assertEqual(self.deposer(b"contenu-altere").status_code, 409)
