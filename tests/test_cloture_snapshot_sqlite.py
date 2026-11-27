"""Régression : les écritures concurrentes ne peuvent pas traverser la clôture.

Test SQLite réel en WAL, indépendant des migrations Django (couvertes séparément).
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from threading import Event, Thread
from unittest.mock import patch

from apps.core.cloture_annuelle_sqlite import preparer_exercice_sqlite


class SnapshotClotureTests(unittest.TestCase):
    def test_verrou_attend_les_ecritures_engagees_et_bloque_les_suivantes(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            source = racine / "n.sqlite3"
            cible = racine / "n1.sqlite3"
            with sqlite3.connect(source) as db:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("CREATE TABLE soldes (montant INTEGER NOT NULL)")
                db.execute("INSERT INTO soldes VALUES (100)")

            ecriture_prete = Event()
            liberer_ecriture = Event()
            erreurs_ecriture = []

            def ecriture_deja_engagee():
                try:
                    with sqlite3.connect(source, timeout=10) as concurrent:
                        concurrent.execute("BEGIN IMMEDIATE")
                        concurrent.execute("UPDATE soldes SET montant=200")
                        ecriture_prete.set()
                        if not liberer_ecriture.wait(10):
                            raise TimeoutError("le scénario n'a pas libéré l'écriture initiale")
                except Exception as exc:
                    erreurs_ecriture.append(exc)

            ecrivain = Thread(target=ecriture_deja_engagee, daemon=True)
            ecrivain.start()
            self.assertTrue(ecriture_prete.wait(5), "l'écriture concurrente initiale n'a pas démarré")

            valeurs = {}
            resultat_fermeture = {}
            fermeture_demarree = Event()

            def initialiser(origine, nouvelle):
                valeurs["referentiel"] = origine.execute(
                    "SELECT montant FROM soldes"
                ).fetchone()[0]
                nouvelle.execute("CREATE TABLE ouverture (montant INTEGER)")
                # Une nouvelle écriture doit être bloquée pendant le verrou
                # BEGIN IMMEDIATE, y compris en mode WAL.
                try:
                    with sqlite3.connect(source, timeout=0.1) as concurrent:
                        concurrent.execute("UPDATE soldes SET montant=300")
                except sqlite3.OperationalError as exc:
                    valeurs["ecriture_pendant_cloture"] = "bloquée" if "locked" in str(exc).lower() else str(exc)
                else:
                    raise AssertionError("une écriture concurrente a traversé le verrou annuel")

            def reporter(origine, nouvelle):
                valeurs["report"] = origine.execute(
                    "SELECT montant FROM soldes"
                ).fetchone()[0]
                nouvelle.execute("INSERT INTO ouverture VALUES (?)", (valeurs["report"],))

            def fermer():
                fermeture_demarree.set()
                try:
                    with patch(
                        "apps.core.cloture_annuelle_sqlite.lire_catalogue",
                        return_value=[{"id": "n", "moteur": "sqlite", "cloture": False, "base": str(source)}],
                    ), patch(
                        "apps.core.cloture_annuelle_sqlite.verifier_base_sqlite",
                        side_effect=lambda chemin: chemin,
                    ), patch(
                        "apps.core.cloture_annuelle_sqlite.publier_exercice_sqlite_valide",
                        return_value={"id": "n1"},
                    ):
                        resultat_fermeture["valeur"] = preparer_exercice_sqlite(
                            racine / "catalogue.json", "n", cible, "n1",
                            initialiser, reporter,
                        )
                except Exception as exc:
                    resultat_fermeture["erreur"] = exc

            fermeture = Thread(target=fermer, daemon=True)
            fermeture.start()
            self.assertTrue(fermeture_demarree.wait(5))
            # La clôture attend le writer déjà engagé ; une fois celui-ci validé,
            # son snapshot doit donc inclure 200, jamais l'ancien solde 100.
            liberer_ecriture.set()
            ecrivain.join(15)
            fermeture.join(15)
            self.assertFalse(ecrivain.is_alive(), "l'écriture initiale est restée bloquée")
            self.assertFalse(fermeture.is_alive(), "la clôture est restée bloquée")
            self.assertEqual(erreurs_ecriture, [])
            self.assertNotIn("erreur", resultat_fermeture, resultat_fermeture.get("erreur"))
            self.assertEqual(resultat_fermeture["valeur"], {"id": "n1"})
            self.assertEqual(valeurs, {
                "referentiel": 200,
                "report": 200,
                "ecriture_pendant_cloture": "bloquée",
            })
            with sqlite3.connect(source) as db:
                self.assertEqual(db.execute("SELECT montant FROM soldes").fetchone()[0], 200)
            with sqlite3.connect(cible) as db:
                self.assertEqual(db.execute("SELECT montant FROM ouverture").fetchone()[0], 200)


if __name__ == "__main__":
    unittest.main()
