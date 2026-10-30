import base64
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, SimpleTestCase
from django.urls import reverse

from . import licence as l
from .models import EtatLicence, LicenceDeposee
from .stockage import PREFIXE


class DistributionLicenceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.admin = get_user_model().objects.create_superuser("editeur-test", "", "Essai-2030-ok")

    def setUp(self):
        self.privee = Ed25519PrivateKey.generate()
        self.publique = self.privee.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.patch = mock.patch("apps.licences.cle_editeur.CLES", [base64.b64encode(self.publique).decode()])
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.client.force_login(self.admin)
        l.oublier()
        self.addCleanup(l.oublier)

    def fichier_licence(self):
        d = {"version": 1, "numero": "TEST-2030", "client": "Société Fictive", "edition": "transport",
             "machine": l.empreinte_machine(), "postes": 5, "valable_jusqu_au": "", "maj_jusqu_au": ""}
        return SimpleUploadedFile("licence.erplic", l.ecrire(d, self.privee.sign(l.canonique(d))).encode())

    def test_code_stocke_protege_et_non_affiche_sur_la_page(self):
        code = l.fc.installation_courte_creer()
        self.client.post(reverse("licence"), {"action": "installation", "cle": code})
        self.assertTrue(EtatLicence.objects.get().cle_installation.startswith(PREFIXE))
        self.assertNotIn(code, EtatLicence.objects.get().cle_installation)
        self.assertEqual(l.cle_installation()["texte"], code)
        self.assertNotContains(self.client.get(reverse("licence")), code)
        with mock.patch.object(l, "_identifiant_machine", return_value="autre-ordinateur"):
            self.assertIsNone(l.cle_installation())

    def test_ancien_fichier_converti_sans_suppression_avant_ecriture(self):
        with tempfile.TemporaryDirectory() as dossier:
            clair = Path(dossier, "cle-installation.txt")
            clair.write_text("code fictif")
            l.proteger_ancienne_installation(dossier)
            self.assertFalse(clair.exists())
            contenu = Path(dossier, "installation.dat").read_text()
            self.assertNotIn("code fictif", contenu)
            self.assertEqual(l.ouvrir_stockage(contenu), "code fictif")
            clair.write_text("autre code fictif")
            with mock.patch.object(l, "proteger_stockage", side_effect=OSError("disque plein")):
                with self.assertRaises(OSError):
                    l.proteger_ancienne_installation(dossier)
            self.assertTrue(clair.exists())

    def test_selection_fichiers_public_et_licence_sans_copie_manuelle(self):
        reponse = self.client.post(reverse("licence"), {"action": "fichier", "fichier": self.fichier_licence(),
                "verification": SimpleUploadedFile("parametres.dat", b"ERPID\x01" + self.publique)}, follow=True)
        self.assertContains(reponse, "installée pour Société Fictive")
        self.assertTrue(LicenceDeposee.objects.get().valide)

    def test_mauvais_editeur_ou_coffre_prive_refuse(self):
        for contenu in (b"ERPID\x01" + b"x" * 32, b"-----BEGIN ENCRYPTED PRIVATE KEY-----\nsecret"):
            self.client.post(reverse("licence"), {"action": "fichier", "fichier": self.fichier_licence(),
                "verification": SimpleUploadedFile("fichier.dat", contenu)})
            self.assertFalse(LicenceDeposee.objects.exists())

    def test_copie_licence_sur_autre_machine_refusee(self):
        fichier = self.fichier_licence()
        with mock.patch.object(l, "empreinte_machine", return_value="AUTRE-MACHINE"):
            self.client.post(reverse("licence"), {"action": "fichier", "fichier": fichier})
        self.assertFalse(LicenceDeposee.objects.filter(valide=True).exists())


class IdentiteCompileeTests(SimpleTestCase):
    def test_variable_de_simulation_ignoree_dans_programme_compile(self):
        with mock.patch.dict(os.environ, {"ERP_MACHINE_ID": "valeur-copiee"}), mock.patch.object(sys, "frozen", True, create=True):
            self.assertNotEqual(l._identifiant_machine(), "valeur-copiee")

    def test_aucune_autorite_remplacable_dans_programme_compile(self):
        with mock.patch.object(sys, "frozen", True, create=True), mock.patch("apps.licences.cle_editeur.CLES", []):
            self.assertEqual(l.cles_publiques(), [])

    def test_documentation_cliente_limitee(self):
        from django.conf import settings

        spec = (settings.BASE_DIR / "deploy/executable/erp_ohada.spec").read_text()
        installateur = (settings.BASE_DIR / "deploy/installateur/erp_ohada.iss").read_text(encoding="utf-8-sig")
        self.assertIn('documentation / "GUIDE-CLIENT.txt"', spec)
        self.assertNotIn('copytree(RACINE / "docs"', spec)
        self.assertNotIn("cle-installation.txt", installateur)
