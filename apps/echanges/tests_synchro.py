"""Synchronisation automatique par boîte aux lettres : lots chiffrés, dossier partagé ou relais Internet.

Les dossiers (direction, Douala, relais) sont des bases séparées, lancées dans des processus distincts, comme sur
des serveurs différents : ils ne partagent que la boîte aux lettres.
"""
import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from django.test import SimpleTestCase

from . import lots
from .scenario import RACINE, Dossier, lots_de
from .synchro import DossierPartage, chiffrer, dechiffrer

ECRITURE = """
import datetime, json
from apps.comptabilite.models import Compte, Journal
from apps.comptabilite.services import creer_ecriture
for n, i in (("6222000", "Locations de bâtiments"), ("5711000", "Caisse")):
    Compte.objects.get_or_create(numero=n, defaults={{"intitule": i}})
creer_ecriture(Journal.objects.get(code="OD"), datetime.date.today(), "{libelle}",
               [{{"compte": Compte.objects.get(numero="6222000"), "debit": 1000}},
                {{"compte": Compte.objects.get(numero="5711000"), "credit": 1000}}])
print(json.dumps(1))"""

RECUES = """
import json
from apps.comptabilite.models import Ecriture
print(json.dumps(sorted(Ecriture.objects.filter(site_origine="DLA").values_list("libelle", flat=True))))"""

DEMANDE = """
import json
from apps.comptabilite.models import Ecriture
from apps.echanges import corrections
d = corrections.demander(Ecriture.objects.filter(site_origine="DLA").first(), "Compte à revoir", "", "chef")
print(json.dumps(d.numero))"""

STATUT = """
import json
from apps.echanges.models import DemandeCorrection
print(json.dumps({d.numero: d.statut for d in DemandeCorrection.objects.all()}))"""


class ChiffrementTests(SimpleTestCase):
    def test_aller_retour_et_refus(self):
        lot = b'{"faits": [1, 2, 3]}' * 50
        c = chiffrer(lot, "cle-partagee", "DLA", "SIEGE")
        self.assertNotIn(b"faits", c)                                       # la boîte ne lit rien
        self.assertEqual(dechiffrer(c, "cle-partagee", "DLA", "SIEGE"), lot)
        self.assertNotEqual(c, chiffrer(lot, "cle-partagee", "DLA", "SIEGE"))   # nonce différent à chaque fois
        abime = c[:-1] + bytes([c[-1] ^ 1])
        for essai in (lambda: dechiffrer(c, "autre-cle", "DLA", "SIEGE"),     # mauvaise clé
                      lambda: dechiffrer(c, "cle-partagee", "YDE", "SIEGE"),  # autre expéditeur
                      lambda: dechiffrer(c, "cle-partagee", "SIEGE", "DLA"),  # renvoyé dans l'autre sens
                      lambda: dechiffrer(abime, "cle-partagee", "DLA", "SIEGE"),
                      lambda: dechiffrer(b"PK\x03\x04 pas un lot", "cle-partagee", "DLA", "SIEGE")):
            with self.assertRaises(lots.LotInvalide):
                essai()

    def test_dossier_partage(self):
        with tempfile.TemporaryDirectory() as racine:
            b = DossierPartage(racine)
            b.deposer("SIEGE", "a.erpx.chiffre", b"1")
            self.assertEqual(b.lister("SIEGE"), ["a.erpx.chiffre"])
            self.assertEqual(b.lister("DLA"), [])
            self.assertEqual(b.lire("SIEGE", "a.erpx.chiffre"), b"1")
            b.retirer("SIEGE", "a.erpx.chiffre")
            self.assertEqual(b.lister("SIEGE"), [])
            self.assertEqual(list(Path(racine, "SIEGE").iterdir()), [])     # pas de fichier provisoire oublié


def _installer(travail):
    siege, dla = Dossier(travail, "siege"), Dossier(travail, "douala")
    for d in (siege, dla):
        d.creer()
    siege.manage("echanges", "siege", "--code", "SIEGE", "--nom", "Direction")
    siege.manage("echanges", "agence", "--code", "DLA", "--nom", "Agence de Douala")
    dla.manage("echanges", "installer",
               lots_de(siege.manage("echanges", "installation", "--agence", "DLA", "--dossier", travail))[0])
    return siege, dla


class SynchronisationDossierPartageTests(SimpleTestCase):
    def test_montee_descente_et_rien_de_vide(self):
        with tempfile.TemporaryDirectory() as travail:
            siege, dla = _installer(travail)
            boite = str(Path(travail) / "boite")
            sync = ("echanges", "synchroniser", "--dossier-partage", boite)
            dla.py(ECRITURE.format(libelle="Loyer d'octobre"))
            self.assertIn("1 lot(s) envoyé(s)", dla.manage(*sync))
            self.assertEqual(len(list(Path(boite, "SIEGE").glob("*.erpx.chiffre"))), 1)
            self.assertIn("1 lot(s) reçu(s)", siege.manage(*sync))
            self.assertEqual(siege.py(RECUES), ["Loyer d'octobre"])
            self.assertEqual(list(Path(boite, "SIEGE").glob("*")), [])       # retiré après intégration

            # La direction signale l'erreur : la demande descend, l'accusé de réception remonte
            numero = siege.py(DEMANDE)
            siege.manage(*sync)
            dla.manage(*sync)
            self.assertEqual(dla.py(STATUT), {numero: "RECUE"})
            siege.manage(*sync)
            self.assertEqual(siege.py(STATUT), {numero: "RECUE"})

            # Rien de nouveau : aucun lot vide n'est déposé
            for d in (siege, dla):
                self.assertIn("0 lot(s) envoyé(s) · 0 lot(s) reçu(s)", d.manage(*sync))

            # Un fichier étranger dans la boîte est signalé et laissé en place, sans rien bloquer
            Path(boite, "SIEGE", "photo.erpx.chiffre").write_bytes(b"x")
            dla.py(ECRITURE.format(libelle="Loyer de novembre"))
            dla.manage(*sync)
            sortie = siege.manage(*sync)
            self.assertIn("fichier inattendu", sortie)
            self.assertEqual(siege.py(RECUES), ["Loyer d'octobre", "Loyer de novembre"])
            self.assertTrue(Path(boite, "SIEGE", "photo.erpx.chiffre").exists())


def _port_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class SynchronisationRelaisInternetTests(SimpleTestCase):
    """Bout en bout : un vrai serveur relais (sa propre base), l'agence et la direction passent par HTTP."""

    def test_par_le_relais(self):
        with tempfile.TemporaryDirectory() as travail:
            siege, dla = _installer(travail)
            relais = Dossier(travail, "relais")
            relais.env.update(RELAIS_ACTIF="1", RELAIS_DOSSIER=str(Path(travail) / "stock-relais"), DEBUG="0",
                              ALLOWED_HOSTS="127.0.0.1")
            relais.manage("migrate", "-v0")
            jetons = {code: relais.manage("relais_site", "--code", code).strip().splitlines()[-1] for code in ("SIEGE", "DLA")}
            port = _port_libre()
            serveur = subprocess.Popen([sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
                                       cwd=RACINE, env=relais.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.addCleanup(serveur.wait, 10)
            self.addCleanup(serveur.terminate)
            url = f"http://127.0.0.1:{port}"
            for _ in range(100):
                try:
                    urllib.request.urlopen(f"{url}/relais/v1/boites/SIEGE/", timeout=1)
                except urllib.error.HTTPError:
                    break                                                  # 401 : le serveur répond
                except OSError:
                    time.sleep(0.2)

            def sync(dossier, code):
                return dossier.manage("echanges", "synchroniser", "--relais-url", url, "--relais-jeton", jetons[code])

            dla.py(ECRITURE.format(libelle="Loyer d'octobre"))
            self.assertIn("1 lot(s) envoyé(s)", sync(dla, "DLA"))
            self.assertIn("1 lot(s) reçu(s)", sync(siege, "SIEGE"))
            self.assertEqual(siege.py(RECUES), ["Loyer d'octobre"])
            self.assertEqual(relais.py("from apps.relais.models import LotDepose; import json; "
                                       "print(json.dumps(LotDepose.objects.count()))"), 0)
            # Le relais ne garde rien de lisible : seuls des lots chiffrés y transitent
            numero = siege.py(DEMANDE)
            sync(siege, "SIEGE")
            stock = list(Path(travail, "stock-relais", "DLA").glob("*"))
            self.assertEqual(len(stock), 1)
            self.assertNotIn(numero.encode(), stock[0].read_bytes())
            sync(dla, "DLA")
            self.assertEqual(dla.py(STATUT), {numero: "RECUE"})
            # Un mauvais jeton : la synchronisation le dit, sans rien casser
            sortie = dla.manage("echanges", "synchroniser", "--relais-url", url, "--relais-jeton", "faux")
            self.assertIn("401", sortie)
