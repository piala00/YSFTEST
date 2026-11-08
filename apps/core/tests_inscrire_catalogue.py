"""Commande `inscrire_base_catalogue` : inscription au catalogue multi-sociétés (atomique, validée)."""
import tempfile
from pathlib import Path

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase

from apps.core.catalogue_societes import lire_catalogue


class InscrireCatalogueTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dossier = Path(self.tmp.name)
        self.catalogue = self.dossier / "societes.json"
        self.base = self.dossier / "erp-2026.sqlite3"
        self.base.write_bytes(b"")                     # fichier présent (contenu non vérifié à l'inscription)

    def _inscrire(self, **kw):
        params = {"catalogue": str(self.catalogue), "societe": "GTC", "agence": "Bertoua",
                  "exercice": "2026", "base": str(self.base)}
        params.update(kw)
        call_command("inscrire_base_catalogue", **params)

    def test_cree_le_catalogue_avec_la_base(self):
        self._inscrire()
        bases = lire_catalogue(self.catalogue)
        self.assertEqual(len(bases), 1)
        self.assertEqual(bases[0]["id"], "gtc-bertoua-2026")
        self.assertEqual(bases[0]["exercice"], "2026")
        self.assertFalse(bases[0]["cloture"])

    def test_doublon_societe_agence_annee_refuse(self):
        self._inscrire()
        autre = self.dossier / "erp-2026-bis.sqlite3"
        autre.write_bytes(b"")
        with self.assertRaises(CommandError):
            self._inscrire(base=str(autre), **{"id": "autre-id"})

    def test_exercice_invalide_refuse(self):
        with self.assertRaises(CommandError):
            self._inscrire(exercice="26")

    def test_catalogue_non_configure_refuse(self):
        with self.assertRaises(CommandError):
            call_command("inscrire_base_catalogue", catalogue="", societe="GTC", agence="B",
                         exercice="2026", base=str(self.base))

    def test_base_absente_refuse(self):
        with self.assertRaises(CommandError):
            self._inscrire(base=str(self.dossier / "absent.sqlite3"))

    def test_seconde_base_annee_differente_ok(self):
        self._inscrire()
        base2 = self.dossier / "erp-2027.sqlite3"
        base2.write_bytes(b"")
        self._inscrire(exercice="2027", base=str(base2))
        self.assertEqual(len(lire_catalogue(self.catalogue)), 2)
