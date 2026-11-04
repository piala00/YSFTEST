"""Contrôles du catalogue de bases, sans modification des bases existantes."""
import json
import tempfile
from pathlib import Path
from django.test import SimpleTestCase
from apps.core.catalogue_societes import lire_catalogue, regrouper, enregistrer_exercice_suivant


class CatalogueSocietesTests(SimpleTestCase):
    def setUp(self):
        self.bases = [
            {"id": "a", "societe": "Transport A", "agence": "Yaoundé", "exercice": "2026", "moteur": "sqlite", "base": "a.sqlite3", "cloture": False},
            {"id": "b", "societe": "Transport A", "agence": "Yaoundé", "exercice": "2025", "moteur": "sqlite", "base": "b.sqlite3", "cloture": True},
            {"id": "c", "societe": "Transport B", "agence": "Douala", "exercice": "2026", "moteur": "mssql", "base": "ERP_B", "cloture": False},
        ]

    def test_regroupement_et_cloture(self):
        self.assertEqual([g["societe"] for g in regrouper(self.bases)], ["Transport A", "Transport B"])
        self.assertEqual([b["id"] for b in regrouper(self.bases)[0]["agences"][0]["exercices"]], ["a"])
        self.assertEqual([b["id"] for b in regrouper(self.bases, afficher_clotures=True)[0]["agences"][0]["exercices"]], ["a", "b"])

    def test_recherche(self):
        self.assertEqual([g["societe"] for g in regrouper(self.bases, "DOUALA")], ["Transport B"])
        self.assertEqual(regrouper(self.bases, "2025"), [])
        self.assertEqual(len(regrouper(self.bases, "2025", afficher_clotures=True)), 1)

    def test_lecture_et_validation(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "societes.json"
            self.assertEqual(lire_catalogue(fichier), [])
            fichier.write_text(json.dumps({"version": 1, "bases": self.bases}), encoding="utf-8")
            self.assertEqual(len(lire_catalogue(fichier)), 3)
            fichier.write_text(json.dumps({"version": 1, "bases": self.bases * 2}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dupliqué"):
                lire_catalogue(fichier)

    def test_publication_annuelle_et_lien_historique(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "societes.json"
            fichier.write_text(json.dumps({"version": 1, "bases": self.bases}), encoding="utf-8")
            suivante = enregistrer_exercice_suivant(fichier, "a", "a2027.sqlite3", "a-2027")
            self.assertEqual(suivante["exercice"], "2027")
            self.assertEqual(suivante["exercice_precedent"], "a")
            bases = lire_catalogue(fichier)
            self.assertEqual(len(bases), 4)
            self.assertTrue(next(b for b in bases if b["id"] == "a")["cloture"])
            self.assertEqual([b["id"] for b in regrouper(bases)[0]["agences"][0]["exercices"]], ["a-2027"])
            avant = fichier.read_bytes()
            with self.assertRaisesRegex(ValueError, "déjà clôturé"):
                enregistrer_exercice_suivant(fichier, "a", "autre.sqlite3", "autre")
            self.assertEqual(fichier.read_bytes(), avant)

    def test_refus_doublons_sans_modifier_catalogue(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "societes.json"
            fichier.write_text(json.dumps({"version": 1, "bases": self.bases}), encoding="utf-8")
            avant = fichier.read_bytes()
            for identifiant, base in (("c", "nouvelle.sqlite3"), ("nouvelle", "a.sqlite3"), ("", "nouvelle.sqlite3")):
                with self.subTest(identifiant=identifiant, base=base):
                    with self.assertRaises(ValueError):
                        enregistrer_exercice_suivant(fichier, "a", base, identifiant)
                    self.assertEqual(fichier.read_bytes(), avant)

    def test_refus_doublons_physiques_et_exercices(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "societes.json"
            for changement, message in (
                ({"id": "d", "societe": "Autre", "agence": "Nord", "exercice": "2028", "moteur": "sqlite", "base": "a.sqlite3"}, "physique"),
                ({"id": "d", "societe": "transport a", "agence": "YAOUNDÉ", "exercice": "2026", "moteur": "sqlite", "base": "nouvelle.sqlite3"}, "Exercice"),
                ({"id": "d", "societe": "Autre", "agence": "Nord", "exercice": "2028", "moteur": "mssql", "base": "erp_b"}, "physique"),
            ):
                with self.subTest(changement=changement):
                    fichier.write_text(json.dumps({"version": 1, "bases": self.bases + [changement]}), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        lire_catalogue(fichier)

    def test_publication_refuse_base_sqlserver_meme_nom_casse_differente(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "societes.json"
            fichier.write_text(json.dumps({"version": 1, "bases": self.bases}), encoding="utf-8")
            avant = fichier.read_bytes()
            with self.assertRaisesRegex(ValueError, "base déjà enregistrée"):
                enregistrer_exercice_suivant(fichier, "c", "erp_b", "c-2027")
            self.assertEqual(fichier.read_bytes(), avant)

    def test_publication_refuse_exercice_meme_agence_casse_differente(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "societes.json"
            bases = self.bases + [{
                "id": "futur", "societe": "transport a", "agence": "YAOUNDÉ",
                "exercice": "2027", "moteur": "sqlite", "base": "futur.sqlite3",
                "cloture": False,
            }]
            fichier.write_text(json.dumps({"version": 1, "bases": bases}), encoding="utf-8")
            avant = fichier.read_bytes()
            with self.assertRaisesRegex(ValueError, "exercice suivant déjà enregistré"):
                enregistrer_exercice_suivant(fichier, "a", "nouveau.sqlite3", "a-2027")
            self.assertEqual(fichier.read_bytes(), avant)

    def test_liens_historiques_incoherents_refuses(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "societes.json"
            parent = {**self.bases[0], "cloture": True}
            enfant = {
                "id": "a-2027", "societe": "Transport A", "agence": "Yaoundé",
                "exercice": "2027", "moteur": "sqlite", "base": "a2027.sqlite3",
                "cloture": False, "exercice_precedent": "a",
            }
            fichier.write_text(json.dumps({"version": 1, "bases": [parent, enfant]}), encoding="utf-8")
            self.assertEqual(len(lire_catalogue(fichier)), 2)
            for modification in (
                {"exercice_precedent": "inconnu"},
                {"exercice_precedent": "a-2027"},
                {"societe": "Autre"},
                {"agence": "Douala"},
                {"exercice": "2028"},
            ):
                with self.subTest(modification=modification):
                    fichier.write_text(json.dumps({
                        "version": 1, "bases": [parent, {**enfant, **modification}],
                    }), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "Lien historique"):
                        lire_catalogue(fichier)
            fichier.write_text(json.dumps({
                "version": 1, "bases": [{**parent, "cloture": False}, enfant],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Lien historique"):
                lire_catalogue(fichier)
