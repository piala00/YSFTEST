"""Le même fichier d'autorisation est revérifié à chaque installation, sans état local résiduel."""
import base64
import datetime
import hashlib
from pathlib import Path
import tempfile
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.test import SimpleTestCase

from . import licence as l
from .installation import autoriser
from deploy.installateur.controle import main


class InstallationTests(SimpleTestCase):
    def setUp(self):
        self.privee = Ed25519PrivateKey.generate()
        publique = self.privee.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.key_id = hashlib.sha256(publique).hexdigest().upper()
        p = mock.patch.object(l, "cles_publiques", return_value=[base64.b64encode(publique).decode()])
        p.start()
        self.addCleanup(p.stop)
        p = mock.patch.object(l, "empreinte_machine", return_value="MACHINE-FICTIVE")
        p.start()
        self.addCleanup(p.stop)

    def fichier(self, **changements):
        d = {"version": 1, "reference": "AAAAAA-AAAAAA-AAAAAA-AAAAAA", "edition": "toutes",
             "machine": "MACHINE-FICTIVE", "key_id": self.key_id, "valable_jusqu_au": None}
        d.update(changements)
        return l.fc.autorisation_texte(d, self.privee.sign(l.fc.DOMAINE_AUTORISATION+l.canonique(d))).encode()

    def test_installation_puis_reinstallation_verifient_le_fichier(self):
        for edition in ("transport", "commerce"):
            fichier = self.fichier()
            self.assertEqual(autoriser(fichier, edition)["machine"], "MACHINE-FICTIVE")
            self.assertEqual(autoriser(fichier, edition)["edition"], edition)
            d, s = l.fc.autorisation_lire(fichier)
            d["machine"] = "falsifiee"
            with self.assertRaisesRegex(l.LicenceInvalide, "signature"):
                autoriser(l.fc.autorisation_texte(d, s).encode(), edition)

    def test_autre_machine_edition_expiration_ou_code_seul_refuses(self):
        for changements in ({"machine": "AUTRE"}, {"edition": "commerce"}, {"valable_jusqu_au": "2020-01-01"},
                              {"version": 99}, {"key_id": "F"*64}):
            with self.subTest(changement=changements), self.assertRaises(l.LicenceInvalide):
                autoriser(self.fichier(**changements), "transport")
        for contenu in (b"ABCDEF-GHIJKL-MNOPQR-STUVWX", b"x" * 65537, b"faux"):
            with self.assertRaises(l.LicenceInvalide):
                autoriser(contenu, "transport")
        d = {"version": 1, "numero": "LIC-2026-0001", "edition": "transport", "machine": "MACHINE-FICTIVE"}
        with self.assertRaisesRegex(l.LicenceInvalide, "licence d'exploitation"):
            autoriser(l.ecrire(d, self.privee.sign(l.canonique(d))).encode(), "transport")

    def test_absence_identite_ne_peut_autoriser_une_installation(self):
        with mock.patch.object(l, "cles_publiques", return_value=[]), self.assertRaises(l.LicenceInvalide):
            autoriser(self.fichier(), "transport")

    def test_controle_embarque_codes_de_sortie_et_rapport(self):
        with tempfile.TemporaryDirectory() as dossier:
            rapport = Path(dossier) / "rapport.txt"
            fichier = Path(dossier) / "fictive.erpinst"
            self.assertEqual(main(["--edition", "transport", "--rapport", str(rapport)]), 0)
            self.assertEqual(rapport.read_text(), "T-MACHINE-FICTIVE")
            fichier.write_bytes(self.fichier())
            self.assertEqual(main(["--edition", "transport", "--rapport", str(rapport), "--verifier", str(fichier)]), 0)
            fichier.write_text("faux")
            self.assertEqual(main(["--edition", "transport", "--rapport", str(rapport), "--verifier", str(fichier)]), 2)
            self.assertIn("refusée", rapport.read_text())
            cible = Path(dossier) / "ne-pas-marquer"
            self.assertEqual(main(["--edition", "transport", "--rapport", str(rapport), "--verifier", str(fichier),
                                   "--marquer-programme", str(cible)]), 2)
            self.assertFalse(cible.exists())

    def test_emission_avec_identite_existante_sans_societe(self):
        from deploy.licences.licences import main as outil
        with tempfile.TemporaryDirectory() as dossier:
            coffre = Path(dossier) / "coffre.dat"
            coffre.write_bytes(self.privee.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                                                        serialization.BestAvailableEncryption(b"Fictif-2026-Test")))
            with mock.patch.dict("os.environ", {"ERP_LICENCES_MDP": "Fictif-2026-Test"}):
                self.assertEqual(outil(["autoriser-installation", "--cle", str(coffre), "--code", "T-AAAA-AAAA-AAAA-AAAA",
                                       "--jusqu-au", (datetime.date.today()+datetime.timedelta(days=2)).isoformat(), "--sortie", dossier]), 0)
            fichier = next(Path(dossier).glob("*.erpinst"))
            d = autoriser(fichier.read_bytes(), "transport", machine="AAAA-AAAA-AAAA-AAAA")
            self.assertEqual(d["key_id"], self.key_id)
            self.assertEqual(list(Path(dossier).glob("*.erpinst")), [fichier])
