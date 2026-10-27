"""Gestion de la base de données : état, vérifier, réparer, optimiser, sauvegarde et restauration SQL Server,
changement de moteur (copie contrôlée). Chaque essai tourne sur une vraie base séparée, dans son propre processus.
Les essais SQL Server tournent quand un serveur d'essai est donné (contrôle « tests-sqlserver », ou
ERP_ESSAI_SQLSERVER_HOTE / _UTILISATEUR / _MDP en local)."""
import os
import tempfile
import unittest
import uuid

from django.test import SimpleTestCase

from apps.echanges.scenario import Dossier

if os.environ.get("DB_ENGINE") == "mssql":
    SERVEUR = {"hote": os.environ.get("DB_HOST", "localhost"), "utilisateur": os.environ.get("DB_USER", ""),
               "mdp": os.environ.get("DB_PASSWORD", "")}
elif os.environ.get("ERP_ESSAI_SQLSERVER_HOTE"):
    SERVEUR = {"hote": os.environ["ERP_ESSAI_SQLSERVER_HOTE"], "utilisateur": os.environ.get("ERP_ESSAI_SQLSERVER_UTILISATEUR", "sa"),
               "mdp": os.environ.get("ERP_ESSAI_SQLSERVER_MDP", "")}
else:
    SERVEUR = None

ETAT = """
import json
from apps.core import base_donnees as bd
d = bd.info()
intacte, messages = bd.verifier()
print(json.dumps({"moteur": d["moteur"], "tables": d["tables"], "taille": d["taille"], "intacte": intacte,
                  "optimiser": bd.optimiser(), "reparer": bd.reparer()[0]}))"""

COMPTES = """
import json
from django.contrib.auth.models import User
from apps.comptabilite.models import Compte
print(json.dumps([sorted(User.objects.values_list("username", flat=True)), Compte.objects.count()]))"""


def dossier_sqlserver(travail, nom):
    d = Dossier(travail, nom)
    d.env.update(DB_ENGINE="mssql", DB_HOST=SERVEUR["hote"], DB_USER=SERVEUR["utilisateur"], DB_PASSWORD=SERVEUR["mdp"],
                 DB_NAME=f"ERP_ESSAI_{nom.upper()}_{uuid.uuid4().hex[:6]}", DB_PYTHON_DRIVER="mssql_python",
                 DB_EXTRA_PARAMS="TrustServerCertificate=yes")
    d.env.pop("SQLITE_FICHIER", None)
    return d


class BaseSQLiteTests(SimpleTestCase):
    def test_etat_verifier_reparer_et_changer_de_moteur(self):
        with tempfile.TemporaryDirectory() as travail:
            source = Dossier(travail, "source")
            source.creer()
            source.manage("shell", "-c", "from django.contrib.auth.models import User; User.objects.create_superuser('chef', '', 'Chef-2026-ok')")
            etat = source.py(ETAT)
            self.assertEqual((etat["moteur"], etat["intacte"], etat["reparer"]), ("sqlite", True, True))
            self.assertGreater(etat["tables"], 50)
            self.assertGreater(etat["taille"], 0)
            self.assertIn("compactée", etat["optimiser"])
            # Changement vers un autre fichier : copie contrôlée, rien ne change dans la base d'origine
            cible = f"{travail}/nouvelle.sqlite3"
            lignes = source.py(f"""
import json
from apps.core import base_donnees as bd
print(json.dumps(bd.changer_de_moteur(bd.reglage_sqlite("{cible}"))))""")
            self.assertGreater(lignes, 100)
            nouvelle = Dossier(travail, "nouvelle")
            self.assertEqual(nouvelle.py(COMPTES), source.py(COMPTES))
            # Une base d'un autre logiciel est refusée et laissée intacte
            import sqlite3

            with sqlite3.connect(f"{travail}/autre.sqlite3") as c:
                c.execute("CREATE TABLE F_COMPTET (CT_Num TEXT)")
            refus = source.py(f"""
import json
from apps.core import base_donnees as bd
try:
    bd.changer_de_moteur(bd.reglage_sqlite("{travail}/autre.sqlite3"))
    print(json.dumps("accepté"))
except Exception as exc:
    print(json.dumps(str(exc)))""")
            self.assertIn("pas une base de l'ERP", refus)
            with sqlite3.connect(f"{travail}/autre.sqlite3") as c:
                self.assertEqual(c.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0], 1)


@unittest.skipUnless(SERVEUR, "pas de SQL Server d'essai")
class BaseSQLServerTests(SimpleTestCase):
    def test_sqlite_vers_sqlserver_puis_gestion_et_retour(self):
        with tempfile.TemporaryDirectory() as travail:
            source = Dossier(travail, "source")
            source.creer()
            source.manage("shell", "-c", "from django.contrib.auth.models import User; User.objects.create_superuser('chef', '', 'Chef-2026-ok')")
            serveur = dossier_sqlserver(travail, "bascule")
            base = serveur.env["DB_NAME"]
            reglage = f'bd.reglage_sqlserver("{SERVEUR["hote"]}", "{base}", "{SERVEUR["utilisateur"]}", "{SERVEUR["mdp"]}")'
            essai = source.py(f"""
import json
from apps.core import base_donnees as bd
r = {reglage}
avant = bd.tester_sqlserver(r)
lignes = bd.changer_de_moteur(r)
print(json.dumps([avant, lignes, bd.tester_sqlserver(r)]))""")
            self.assertIn("sera créée", essai[0])
            self.assertGreater(essai[1], 100)
            self.assertIn("de l'ERP", essai[2])
            self.assertEqual(serveur.py(COMPTES), source.py(COMPTES))
            try:
                etat = serveur.py(ETAT)
                self.assertEqual((etat["moteur"], etat["intacte"], etat["reparer"]), ("mssql", True, True))
                self.assertGreater(etat["taille"], 0)
                # Sauvegarde native (.bak), puis restauration : la saisie faite après la sauvegarde disparaît
                fichier = serveur.py("""
import json
from apps.core import base_donnees as bd
f = bd.sauvegarder_sqlserver()
assert f in [s["nom"] for s in bd.sauvegardes_sqlserver()]
assert bd.sauvegarder_sqlserver() != f                     # même seconde : jamais le même fichier (régression)
from django.contrib.auth.models import User
User.objects.create_user("apres", "", "Apres-2026-ok")
print(json.dumps(f))""")
                self.assertTrue(fichier.endswith(".bak"))
                serveur.py(f"""
import json
from django.db import connections
from apps.core import base_donnees as bd
print(json.dumps(bd.restaurer_sqlserver(connections.databases["default"], {fichier!r})))""")
                self.assertEqual(serveur.py(COMPTES)[0], ["chef"])
                # Retour vers SQLite
                retour = f"{travail}/retour.sqlite3"
                serveur.py(f"""
import json
from apps.core import base_donnees as bd
print(json.dumps(bd.changer_de_moteur(bd.reglage_sqlite("{retour}"))))""")
                self.assertEqual(Dossier(travail, "retour").py(COMPTES), source.py(COMPTES))
            finally:
                source.py(f"""
from django.db import connections
from apps.core import base_donnees as bd
connections.settings["_m"] = {{**{reglage}, "NAME": "master"}}
with connections["_m"].cursor() as cur:
    cur.execute("ALTER DATABASE [{base}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
    cur.execute("DROP DATABASE [{base}]")
print(1)""")
