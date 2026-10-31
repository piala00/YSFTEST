"""Dossiers fictifs : confirmation, sauvegarde relue, liens, collisions et coexistence des éditions."""
import os
from pathlib import Path
import sqlite3
import tempfile
from unittest import mock

from django.test import SimpleTestCase
from . import nettoyage as n


class NettoyageTests(SimpleTestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.racine = Path(d.name).resolve()
        self.programme = self.racine / "programmes/Transport"
        self.donnees = self.racine / "ERP-OHADA/Transport"
        self.autre = self.racine / "ERP-OHADA/Commerce"
        self.autre.mkdir(parents=True)
        (self.autre / "erp.sqlite3").write_text("Autre édition préservée")
        n.marquer(self.programme, "transport")
        n.marquer(self.donnees, "transport")
        with sqlite3.connect(self.donnees / "erp.sqlite3") as c:
            c.execute("CREATE TABLE essai (texte TEXT)")
            c.execute("INSERT INTO essai VALUES ('Fictif')")
        (self.donnees / "configuration.env").write_text("DB_ENGINE=sqlite\n")
        self.archive = self.racine / "sauvegarde.zip"

    def plan(self):
        return n.inventorier(self.programme, self.donnees, "transport")

    def test_refus_sans_confirmation_et_sauvegarde_verifiee(self):
        plan = self.plan()
        with self.assertRaises(ValueError):
            n.effacer(plan, self.archive)
        with self.assertRaises(OSError):
            n.effacer(plan, self.archive, confirmation=True)
        self.assertTrue((self.donnees / "erp.sqlite3").exists())

    def test_effacement_cible_et_autre_edition_parent_partage_preserves(self):
        plan = self.plan()
        n.sauvegarder(plan, self.archive)
        resultat = n.effacer(plan, self.archive, confirmation=True)
        self.assertEqual(resultat["erreurs"], [])
        self.assertFalse(self.donnees.exists())
        self.assertTrue(self.donnees.parent.exists())
        self.assertEqual((self.autre / "erp.sqlite3").read_text(), "Autre édition préservée")
        n.verifier_sauvegarde(plan, self.archive)
        self.assertTrue(self.archive.with_suffix(".rapport.json").exists())

    def test_fichier_inconnu_sql_externe_et_dossier_inconnu_preserves(self):
        (self.donnees / "notes-utilisateur.txt").write_text("préserver")
        (self.donnees / "autre-base.mdf").write_text("préserver")
        (self.donnees / "dossier-utilisateur-vide").mkdir()
        plan = self.plan()
        n.sauvegarder(plan, self.archive)
        resultat = n.effacer(plan, self.archive, confirmation=True)
        self.assertEqual(len(resultat["conserves"]), 3)
        self.assertTrue((self.donnees / "notes-utilisateur.txt").exists())
        self.assertTrue((self.donnees / "autre-base.mdf").exists())
        self.assertTrue((self.donnees / "dossier-utilisateur-vide").is_dir())

    def test_lien_dur_et_symbolique_ne_detruisent_pas_la_cible(self):
        cible = self.racine / "externe.txt"
        cible.write_text("Fichier extérieur")
        for nom, fabriquer in (("journal.txt", os.link), ("erreur-base.txt", os.symlink)):
            try:
                fabriquer(cible, self.donnees / nom)
            except OSError:
                continue  # privilège des liens symboliques non garanti sur Windows
        plan = self.plan()
        n.sauvegarder(plan, self.archive)
        n.effacer(plan, self.archive, confirmation=True)
        self.assertEqual(cible.read_text(), "Fichier extérieur")

    def test_modification_apres_inventaire_ou_archive_fausse_refusee(self):
        plan = self.plan()
        n.sauvegarder(plan, self.archive)
        (self.donnees / "configuration.env").write_text("modifiée")
        with self.assertRaises(ValueError):
            n.effacer(plan, self.archive, confirmation=True)
        self.assertTrue((self.donnees / "erp.sqlite3").exists())
        (self.donnees / "erp.sqlite3").write_bytes(b"Base corrompue fictive")
        with self.assertRaisesRegex(ValueError, "Contrôle SQLite impossible"):
            n.sauvegarder(self.plan(), self.racine / "corrompue.zip")
        self.assertFalse((self.racine / "corrompue.zip").exists())

    def test_archive_interne_et_collision_journal_refusees_avant_effacement(self):
        plan = self.plan()
        with self.assertRaises(ValueError):
            n.sauvegarder(plan, self.donnees / "dangereux.zip")
        n.sauvegarder(plan, self.archive)
        self.archive.with_suffix(".rapport.json").write_text("existant")
        with self.assertRaises(FileExistsError):
            n.effacer(plan, self.archive, confirmation=True)
        self.assertTrue((self.donnees / "erp.sqlite3").exists())

    def test_dossiers_superposes_et_marqueur_autre_produit_refuses(self):
        with self.assertRaises(ValueError):
            n.inventorier(self.racine, self.donnees, "transport")
        with self.assertRaises(ValueError):
            n.marquer(self.donnees, "commerce")
        (self.donnees / n.MARQUEUR).write_text("commerce")
        plan = self.plan()
        self.assertFalse(any(f["genre"] == "donnees" for f in plan["fichiers"]))
