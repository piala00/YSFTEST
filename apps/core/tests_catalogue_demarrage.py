"""Inscription fail-safe de la base au catalogue au démarrage du poste (deploy/executable)."""
import datetime
import importlib.util
import os
import tempfile
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import TestCase

from apps.core.catalogue_societes import lire_catalogue
from apps.core.models import Exercice, Societe

_spec = importlib.util.spec_from_file_location(
    "erp_ohada_demarrage", settings.BASE_DIR / "deploy" / "executable" / "erp_ohada.py")
lanceur = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lanceur)


class CatalogueDemarrageTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.donnees = Path(self.tmp.name)
        self.base = self.donnees / "erp.sqlite3"
        self.base.write_bytes(b"")                      # fichier présent (contenu non vérifié à l'inscription)
        self.catalogue = self.donnees / "societes.json"
        Exercice.objects.create(code="2026", date_debut=datetime.date(2026, 1, 1),
                                date_fin=datetime.date(2026, 12, 31), cloture=False)

    def _societe(self, termine=True):
        Societe.objects.create(raison_sociale="GTC Transport", assistant_termine=termine)

    def _appeler(self):
        with mock.patch.object(lanceur, "base_sqlite", return_value=self.base), \
             mock.patch.dict(os.environ, {"ERP_CATALOGUE_SOCIETES": str(self.catalogue)}, clear=False):
            lanceur.inscrire_base_au_catalogue(self.donnees)

    def test_inscrit_la_base_quand_societe_nommee(self):
        self._societe(termine=True)
        self._appeler()
        bases = lire_catalogue(self.catalogue)
        self.assertEqual(len(bases), 1)
        self.assertEqual(bases[0]["societe"], "GTC Transport")
        self.assertEqual(bases[0]["exercice"], "2026")
        self.assertEqual(Path(bases[0]["base"]).resolve(), self.base.resolve())

    def test_idempotent_pas_de_doublon(self):
        self._societe(termine=True)
        self._appeler()
        self._appeler()                                 # second démarrage : ne doit rien ajouter
        self.assertEqual(len(lire_catalogue(self.catalogue)), 1)

    def test_attend_que_l_assistant_soit_termine(self):
        self._societe(termine=False)
        self._appeler()
        self.assertFalse(self.catalogue.exists())       # pas de nom définitif → pas d'inscription

    def test_jamais_bloquant_sans_catalogue(self):
        self._societe(termine=True)
        with mock.patch.object(lanceur, "base_sqlite", return_value=self.base), \
             mock.patch.dict(os.environ, {"ERP_CATALOGUE_SOCIETES": ""}, clear=False):
            lanceur.inscrire_base_au_catalogue(self.donnees)   # ne lève pas
        self.assertFalse(self.catalogue.exists())
