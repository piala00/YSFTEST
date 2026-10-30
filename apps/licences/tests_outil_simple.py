"""Contrôles de l'outil d'émission, exécutables sans serveur ni base de données."""
import base64
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from apps.licences import format_cles as fc

RACINE = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("outil_licences_simple", RACINE / "deploy/licences/licences.py")
outil = importlib.util.module_from_spec(spec)
spec.loader.exec_module(outil)


class OutilSimpleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dossier = Path(self.temp.name)
        self.coffre = self.dossier / "editeur"
        self.coffre.mkdir()
        self.mdp = b"Exemple-fictif-uniquement"
        with contextlib.redirect_stdout(io.StringIO()):
            outil.creer_cles(self.coffre, noms_neutres=True, mdp=self.mdp)
        self.chemin = outil.chemin_coffre(self.coffre)

    def test_coffre_neutre_chiffre_compatible(self):
        self.assertEqual(self.chemin.name, "coffre.dat")
        with self.assertRaises((ValueError, TypeError)):
            serialization.load_der_private_key(self.chemin.read_bytes(), password=None)
        with self.assertRaises(SystemExit):
            outil.charger_cle(self.chemin, b"incorrect")
        cle = outil.charger_cle(self.chemin, self.mdp)
        self.assertEqual((self.coffre / "parametres.dat").read_bytes(), b"ERPID\x01" + cle.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw))

    def test_ancien_coffre_toujours_reconnu(self):
        ancien = self.dossier / "ancien"
        with contextlib.redirect_stdout(io.StringIO()):
            outil.creer_cles(ancien, mdp=self.mdp)
        self.assertEqual(outil.chemin_coffre(ancien).name, "cle-privee.pem")
        outil.charger_cle(outil.chemin_coffre(ancien), self.mdp)

    def test_creation_ne_remplace_jamais_identite(self):
        avant = self.chemin.read_bytes()
        with self.assertRaises(SystemExit):
            outil.creer_cles(self.coffre, mdp=self.mdp)
        self.assertEqual(self.chemin.read_bytes(), avant)

    def test_un_deverrouillage_par_session_puis_verrouillage(self):
        session = outil.CoffreSession()
        demander = mock.Mock(return_value=self.mdp)
        cle = session.ouvrir(self.chemin, demander)
        self.assertIs(session.ouvrir(self.chemin, demander), cle)
        self.assertEqual(demander.call_count, 1)
        session.verrouiller()
        self.assertIsNone(session.cle)
        session.ouvrir(self.chemin, demander)
        self.assertEqual(demander.call_count, 2)

    def test_annulation_et_mauvais_mot_de_passe_ne_deverrouillent_pas(self):
        session = outil.CoffreSession()
        self.assertIsNone(session.ouvrir(self.chemin, lambda: None))
        with self.assertRaises(SystemExit):
            session.ouvrir(self.chemin, lambda: b"incorrect")
        self.assertIsNone(session.cle)

    def test_changement_fichier_invalide_le_cache(self):
        session = outil.CoffreSession()
        session.ouvrir(self.chemin, lambda: self.mdp)
        self.chemin.write_bytes(b"fichier invalide")
        with self.assertRaises(SystemExit):
            session.ouvrir(self.chemin, lambda: self.mdp)
        self.assertIsNone(session.cle)

    def test_reference_quatre_groupes_sans_confusion_avec_licence(self):
        code = fc.installation_courte_creer()
        self.assertRegex(code, r"^[A-Z2-7]{6}(?:-[A-Z2-7]{6}){3}$")
        self.assertEqual(fc.installation_courte_normaliser(code.lower().replace("-", " ")), code)
        with self.assertRaises(fc.CleInvalide):
            fc.installation_lire(code)
        with self.assertRaises(fc.CleInvalide):
            fc.activation_lire(code)

    def test_dossier_client_signe_et_notice_sans_secret(self):
        cle = outil.charger_cle(self.chemin, self.mdp)
        sortie = self.dossier / "client"
        a = SimpleNamespace(cle=str(self.chemin), client="Société Démonstration", edition="transport",
                            sortie=str(sortie), courte=True)
        with contextlib.redirect_stdout(io.StringIO()):
            _, code, _ = outil.emettre_installation(a, cle_deverrouillee=cle)
        demande = {"societe": a.client, "materiel": "TEST-SERVEUR", "machine_nom": "POSTE-DEMO", "edition": "transport",
                   "role": "seul", "site": "", "installation": code, "cle_installation": code}
        fichier = self.dossier / "demande.erpdem"
        fichier.write_text(fc.demande_ecrire(demande), encoding="utf-8")
        a.demande = str(fichier)
        a.role = None
        a.postes = 3
        a.definitive = True
        a.maj_jusqu_au = "2030-12-31"
        a.fichier = None
        with contextlib.redirect_stdout(io.StringIO()):
            licence = outil.emettre(a, cle_deverrouillee=cle)
            outil.verifier(licence, sortie / "parametres.dat")
        lignes = licence.read_text().splitlines()
        donnees = json.loads(base64.b64decode(lignes[1]))
        self.assertEqual(donnees["version"], 3)
        self.assertEqual(donnees["installation"], code)
        donnees["postes"] = 99
        with self.assertRaises(InvalidSignature):
            cle.public_key().verify(base64.b64decode(lignes[2]), fc.canonique(donnees))
        notice = licence.with_name(licence.stem + "-LIRE-MOI.txt").read_text()
        self.assertIn(code, notice)
        self.assertIn(a.activation, notice)
        self.assertIn(licence.name, notice)
        self.assertNotIn(self.mdp.decode(), notice)
        self.assertFalse((sortie / "coffre.dat").exists())
        self.assertFalse((sortie / "cle-privee.pem").exists())

    def test_identite_autre_editeur_non_ecrasee(self):
        client = self.dossier / "client"
        cle = outil.charger_cle(self.chemin, self.mdp)
        chemin = outil.ecrire_identite(cle, client)
        avant = chemin.read_bytes()
        with self.assertRaises(SystemExit):
            outil.ecrire_identite(Ed25519PrivateKey.generate(), client)
        self.assertEqual(chemin.read_bytes(), avant)


if __name__ == "__main__":
    unittest.main()
