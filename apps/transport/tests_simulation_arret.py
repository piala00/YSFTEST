"""Arrêt coopératif d'une génération de simulation (G-SIM-04).

Deux niveaux : les marqueurs d'arrêt (apps.core.dossiers_simulation) et le respect de la demande
d'arrêt par la commande « simulation » (s'arrête proprement après la tranche en cours).
"""
import io
import tempfile
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from apps.core import dossiers_simulation as ds


class MarqueurArretTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dossier = Path(self.tmp.name)

    def test_demander_puis_detecter_puis_effacer(self):
        self.assertFalse(ds.arret_demande(self.dossier))
        ds.demander_arret(self.dossier)
        self.assertTrue(ds.arret_demande(self.dossier))
        ds.effacer_arret(self.dossier)
        self.assertFalse(ds.arret_demande(self.dossier))

    def test_effacer_sans_marqueur_ne_leve_pas(self):
        ds.effacer_arret(self.dossier)                     # aucun marqueur : silencieux
        self.assertFalse(ds.arret_demande(self.dossier))

    def test_lien_symbolique_refuse(self):
        cible = self.dossier / "cible"
        cible.write_text("x", encoding="utf-8")
        lien = self.dossier / ".arreter"
        try:
            lien.symlink_to(cible)
        except (OSError, NotImplementedError):
            self.skipTest("liens symboliques indisponibles")
        self.assertFalse(ds.arret_demande(self.dossier))   # un lien n'est jamais un marqueur valide
        with self.assertRaises(ValueError):
            ds.demander_arret(self.dossier)


class SimulationArretTests(TestCase):
    """La commande « simulation » s'arrête après la tranche en cours quand l'arrêt est demandé."""

    def _commande(self, **patch):
        from apps.transport.management.commands.simulation import Command

        commande = Command()
        contexte = (mock.patch("apps.transport.management.commands.simulation.arret_demande", **patch)
                    if patch else mock.patch("apps.transport.management.commands.simulation.arret_demande",
                                             return_value=False))
        with contexte:
            call_command(commande, mois="2026-09", nombre_mois=2, jours=1, vehicules=4, salaries=5,
                         echelle=0.05, forcer=True, graine=1, stdout=io.StringIO())
        return commande

    def test_arret_apres_la_premiere_tranche(self):
        commande = self._commande(return_value=True)       # arrêt demandé dès la fin du 1er mois
        self.assertTrue(commande.interrompu)
        self.assertEqual(len(commande.par_mois), 1)         # 2 mois demandés, 1 seul généré

    def test_sans_arret_les_deux_mois_sont_generes(self):
        commande = self._commande()                         # aucun arrêt demandé
        self.assertFalse(commande.interrompu)
        self.assertEqual(len(commande.par_mois), 2)
