"""Contrôles du catalogue de bases, sans modification des bases existantes."""
import json
import sqlite3
import tempfile
from pathlib import Path
from django.test import SimpleTestCase
from apps.core.catalogue_societes import lire_catalogue, regrouper, enregistrer_exercice_suivant, publier_exercice_sqlite_valide


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

    def test_catalogue_refuse_alias_sqlite_physiques(self):
        import os
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            source = racine / "2026.sqlite3"
            with sqlite3.connect(source) as connexion:
                connexion.execute("CREATE TABLE exemple (id INTEGER)")
            catalogue = racine / "societes.json"
            premiere = {**self.bases[0], "base": str(source)}
            for alias in (str(racine / "sous" / ".." / source.name),
                          str(racine / "alias.sqlite3")):
                if alias.endswith("alias.sqlite3"):
                    try:
                        os.link(source, alias)
                    except (OSError, NotImplementedError):
                        continue
                else:
                    (racine / "sous").mkdir(exist_ok=True)
                seconde = {**self.bases[1], "base": alias}
                catalogue.write_text(json.dumps({
                    "version": 1, "bases": [premiere, seconde],
                }), encoding="utf-8")
                with self.subTest(alias=alias):
                    with self.assertRaisesRegex(ValueError, "physique dupliquée"):
                        lire_catalogue(catalogue)

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

    def test_refus_annees_invalides_et_depassement(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "societes.json"
            for annee in ("26", "20x6", "２０２６", "0000", "9999"):
                with self.subTest(annee=annee):
                    fichier.write_text(json.dumps({"version": 1, "bases": [
                        {**self.bases[0], "exercice": annee},
                    ]}), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "Année"):
                        lire_catalogue(fichier)
            fichier.write_text(json.dumps({"version": 1, "bases": [
                {**self.bases[0], "exercice": "9998"},
            ]}), encoding="utf-8")
            avant = fichier.read_bytes()
            with self.assertRaisesRegex(ValueError, "hors limites"):
                enregistrer_exercice_suivant(fichier, "a", "a9999.sqlite3", "a-9999")
            self.assertEqual(fichier.read_bytes(), avant)

    def test_publication_annee_initiale_conserve_quatre_chiffres(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "societes.json"
            premiere = {**self.bases[0], "exercice": "0001"}
            fichier.write_text(json.dumps({"version": 1, "bases": [premiere]}), encoding="utf-8")
            suivante = enregistrer_exercice_suivant(fichier, "a", "a0002.sqlite3", "a-0002")
            self.assertEqual(suivante["exercice"], "0002")
            self.assertEqual(lire_catalogue(fichier)[-1]["exercice_precedent"], "a")

    def test_publication_sqlite_exige_base_erp_physique(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            catalogue = racine / "societes.json"
            source = {**self.bases[0], "base": str(racine / "source.sqlite3")}
            catalogue.write_text(json.dumps({"version": 1, "bases": [source]}), encoding="utf-8")
            avant = catalogue.read_bytes()
            cible = racine / "2027.sqlite3"
            with self.assertRaisesRegex(ValueError, "fichier SQLite absolu existant requis"):
                publier_exercice_sqlite_valide(catalogue, "a", str(cible), "a-2027")
            self.assertEqual(catalogue.read_bytes(), avant)
            with sqlite3.connect(cible) as connexion:
                connexion.execute("CREATE TABLE table_inconnue (id INTEGER)")
            with self.assertRaisesRegex(ValueError, "base ERP compatible"):
                publier_exercice_sqlite_valide(catalogue, "a", str(cible), "a-2027")
            self.assertEqual(catalogue.read_bytes(), avant)
            with sqlite3.connect(cible) as connexion:
                for table in ("django_migrations", "auth_user", "core_societe"):
                    connexion.execute(f"CREATE TABLE {table} (id INTEGER)")
            suivante = publier_exercice_sqlite_valide(catalogue, "a", str(cible), "a-2027")
            self.assertEqual(suivante["exercice"], "2027")
            self.assertEqual(suivante["base"], str(cible.resolve()))
            self.assertTrue(lire_catalogue(catalogue)[0]["cloture"])

    def test_publication_refuse_meme_base_physique_par_alias(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            source = racine / "source.sqlite3"
            with sqlite3.connect(source) as connexion:
                for table in ("django_migrations", "auth_user", "core_societe"):
                    connexion.execute(f"CREATE TABLE {table} (id INTEGER)")
            catalogue = racine / "societes.json"
            entree = {**self.bases[0], "base": str(source)}
            catalogue.write_text(json.dumps({"version": 1, "bases": [entree]}), encoding="utf-8")
            avant = catalogue.read_bytes()
            alias = str(racine / "sous-dossier" / ".." / "source.sqlite3")
            (racine / "sous-dossier").mkdir()
            with self.assertRaisesRegex(ValueError, "base physique déjà enregistrée"):
                publier_exercice_sqlite_valide(catalogue, "a", alias, "a-2027")
            self.assertEqual(catalogue.read_bytes(), avant)

    def test_publication_refuse_references_sqlite_invalides(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            catalogue = racine / "societes.json"
            catalogue.write_text(json.dumps({"version": 1, "bases": [
                {**self.bases[0], "base": str(racine / "2026.sqlite3")},
            ]}), encoding="utf-8")
            cible = racine / "2027.sqlite3"
            with sqlite3.connect(cible) as connexion:
                for table in ("django_migrations", "auth_user", "core_societe"):
                    connexion.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")
                connexion.execute(
                    "CREATE TABLE reference_test (id INTEGER PRIMARY KEY, "
                    "societe_id INTEGER REFERENCES core_societe(id))"
                )
                connexion.execute("INSERT INTO reference_test VALUES (1, 999)")
            avant = catalogue.read_bytes()
            with self.assertRaisesRegex(ValueError, "références invalides"):
                publier_exercice_sqlite_valide(catalogue, "a", str(cible), "a-2027")
            self.assertEqual(catalogue.read_bytes(), avant)
            self.assertFalse(next(b for b in lire_catalogue(catalogue) if b["id"] == "a")["cloture"])
