"""Commande `cloturer_exercice` : dérivation des paramètres et garde-fous (messages français).

Le moteur de clôture lui-même (création N+1 migrée, reports à nouveau, lien catalogue) est couvert
par apps.core.test_cloture_annuelle_sqlite et tests/test_cloture_django_migree. Ici on vérifie la
couche commande : déduction année/chemins et refus propres sans trace Python.
"""
import json
import tempfile
from pathlib import Path

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase

from apps.core.management.commands.cloturer_exercice import derive_parametres


def _ecrire_catalogue(dossier, bases):
    chemin = Path(dossier) / "societes.json"
    chemin.write_text(json.dumps({"version": 1, "bases": bases}), encoding="utf-8")
    return str(chemin)


class DerivationTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dossier = self.tmp.name

    def _base(self, **surcharges):
        base = {"id": "gtc-bertoua-2025", "societe": "GTC", "agence": "Bertoua",
                "exercice": "2025", "moteur": "sqlite",
                "base": str(Path(self.dossier) / "erp-2025.sqlite3")}
        base.update(surcharges)
        return base

    def test_derive_annee_suivante_et_chemins(self):
        catalogue = _ecrire_catalogue(self.dossier, [self._base()])
        destination, nouvel_identifiant, annee = derive_parametres(catalogue, "gtc-bertoua-2025")
        self.assertEqual(annee, 2026)
        self.assertEqual(nouvel_identifiant, "gtc-bertoua-2026")
        self.assertTrue(destination.endswith("gtc-bertoua-2026.sqlite3"))
        self.assertEqual(str(Path(destination).parent), self.dossier)

    def test_surcharges_respectees(self):
        catalogue = _ecrire_catalogue(self.dossier, [self._base()])
        destination, nouvel_identifiant, annee = derive_parametres(
            catalogue, "gtc-bertoua-2025", destination="/tmp/n1.sqlite3", nouvel_identifiant="autre")
        self.assertEqual((destination, nouvel_identifiant, annee), ("/tmp/n1.sqlite3", "autre", 2026))

    def test_exercice_inconnu_refuse(self):
        catalogue = _ecrire_catalogue(self.dossier, [self._base()])
        with self.assertRaises(CommandError):
            derive_parametres(catalogue, "inexistant")

    def test_exercice_deja_cloture_refuse(self):
        catalogue = _ecrire_catalogue(self.dossier, [self._base(cloture=True)])
        with self.assertRaises(CommandError):
            derive_parametres(catalogue, "gtc-bertoua-2025")

    def test_base_mssql_refusee(self):
        catalogue = _ecrire_catalogue(self.dossier, [self._base(moteur="mssql", base="ERP_2025")])
        with self.assertRaises(CommandError):
            derive_parametres(catalogue, "gtc-bertoua-2025")


class CommandeGardeFousTests(SimpleTestCase):
    def test_catalogue_non_configure(self):
        with self.assertRaises(CommandError):
            call_command("cloturer_exercice", "x", catalogue="")

    def test_catalogue_absent(self):
        with self.assertRaises(CommandError):
            call_command("cloturer_exercice", "x", catalogue="/chemin/inexistant/societes.json")
