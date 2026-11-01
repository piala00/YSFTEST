"""P0 activation : identité intégrée, fichiers émis conservés, deux éditions et refus réels."""
import ast
import base64
import datetime
import os
from pathlib import Path
import sys
import tempfile
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from . import licence as l
from .identite import empreinte, lire_publique, verifier_distribution
from .models import LicenceDeposee
from apps.core.models import Societe
from deploy.executable.personnaliser_identite import personnaliser


class PersonnalisationTests(SimpleTestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.racine = Path(d.name)
        self.cible = self.racine / "apps/licences/cle_editeur.py"
        self.cible.parent.mkdir(parents=True)
        self.cible.write_text("CLES = []\n", encoding="utf-8")
        self.cle = Ed25519PrivateKey.generate()
        self.brut = self.cle.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)

    def test_formats_publics_historiques_et_binaires_meme_identite(self):
        for contenu in (b"ERPID\x01" + self.brut, base64.b64encode(self.brut) + b"\n"):
            with self.subTest(format=contenu[:5]):
                personnaliser(self.racine, contenu, empreinte(self.brut))
                arbre = ast.parse(self.cible.read_text())
                cles = ast.literal_eval(arbre.body[-1].value)
                self.assertEqual(cles, [base64.b64encode(self.brut).decode()])
                self.assertEqual(verifier_distribution(cles)["empreintes_sha256"], [empreinte(self.brut)])

    def test_empreinte_absente_ou_differente_ne_modifie_rien(self):
        for attendue in ("", "F" * 64):
            with self.assertRaises(ValueError):
                personnaliser(self.racine, b"ERPID\x01" + self.brut, attendue)
            self.assertEqual(self.cible.read_text(), "CLES = []\n")

    def test_coffre_prive_et_fichier_invalide_refuses(self):
        coffre = self.cle.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                                       serialization.BestAvailableEncryption(b"Fictif-2026-P0"))
        for contenu in (coffre, b"-----BEGIN PRIVATE KEY-----\nsecret", b"x" * 8193, b"ERPID\x01"):
            with self.assertRaises(ValueError):
                personnaliser(self.racine, contenu, empreinte(self.brut))
            self.assertEqual(self.cible.read_text(), "CLES = []\n")

    def test_rotation_implicite_et_module_deja_compile_refuses(self):
        personnaliser(self.racine, b"ERPID\x01" + self.brut, empreinte(self.brut))
        original = self.cible.read_bytes()
        autre = Ed25519PrivateKey.generate().public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        with self.assertRaisesRegex(ValueError, "rotation"):
            personnaliser(self.racine, b"ERPID\x01" + autre, empreinte(autre))
        self.assertEqual(self.cible.read_bytes(), original)
        (self.cible.parent / "cle_editeur.cp312-win_amd64.pyd").touch()
        with self.assertRaisesRegex(ValueError, "déjà compilée"):
            personnaliser(self.racine, b"ERPID\x01" + self.brut, empreinte(self.brut))

    def test_distribution_ne_peut_pas_devenir_un_essai_implicite(self):
        with self.assertRaisesRegex(ValueError, "commerciale refusée"):
            verifier_distribution([])
        self.assertEqual(verifier_distribution([], version_essai=True)["mode"], "essai-sans-editeur")
        with self.assertRaises(ValueError):
            verifier_distribution([base64.b64encode(self.brut).decode()], version_essai=True)
        with self.assertRaises(ValueError):
            verifier_distribution(["invalide"])


class ActivationDeuxEditionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.admin = get_user_model().objects.create_superuser("activation-fictive", "", "Fictif-2026-P0")

    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.privee = Ed25519PrivateKey.generate()
        brut = self.privee.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        for p in (mock.patch("apps.licences.cle_editeur.CLES", [base64.b64encode(brut).decode()]),
                  mock.patch.object(sys, "frozen", True, create=True),
                  mock.patch.dict(os.environ, {"ERP_DOSSIER_DONNEES": d.name}),
                  mock.patch.object(l, "_registre_lire", return_value=None),
                  mock.patch.object(l, "_registre_ecrire")):
            p.start()
            self.addCleanup(p.stop)
        self.client.force_login(self.admin)
        l.oublier()
        self.addCleanup(l.oublier)

    def fichier(self, edition_cible, **modifications):
        demande = l.demande()
        conditions = {"numero": "LIC-2026-0001", "edition": edition_cible, "role": demande["role"], "postes": 5,
                      "emise_le": datetime.date.today().isoformat(), "valable_jusqu_au": None, "maj_jusqu_au": None}
        donnees = l.fc.licence_donnees(demande, conditions)
        donnees.update(modifications)
        return l.ecrire(donnees, self.privee.sign(l.canonique(donnees)))

    def deposer(self, texte):
        return self.client.post(reverse("licence"), {"action": "fichier",
            "fichier": SimpleUploadedFile("fictive.erplic", texte.encode())}, follow=True)

    def choisir_edition(self, edition):
        Societe.objects.update(activite=edition.upper(), raison_sociale="Société Fictive P0")
        code = l.fc.installation_courte_creer()
        self.client.post(reverse("licence"), {"action": "installation", "cle": code})
        l.oublier()

    def test_licence_seule_deux_editions_et_relecture_persistante(self):
        for edition in ("transport", "commerce"):
            with self.subTest(edition=edition):
                self.choisir_edition(edition)
                texte = self.fichier(edition)
                self.assertContains(self.deposer(texte), "installée pour Société Fictive P0")
                self.assertEqual(LicenceDeposee.objects.filter(valide=True).first().contenu, texte)
                l.oublier()
                self.assertEqual(l.etat().licence["numero"], "LIC-2026-0001")
                self.assertFalse(l.etat().lecture_seule)

    def test_fausse_signature_mauvaise_edition_machine_installation_refusees(self):
        for edition in ("transport", "commerce"):
            self.choisir_edition(edition)
            for modifications in ({"edition": "commerce" if edition == "transport" else "transport"},
                                  {"machine": "AUTRE-MACHINE"}, {"installation": "AUTRE-INSTALLATION"},
                                  {"client": "Autre société"}):
                with self.subTest(edition=edition, modification=modifications):
                    self.assertContains(self.deposer(self.fichier(edition, **modifications)), "Refusé")
                    self.assertFalse(LicenceDeposee.objects.filter(valide=True).exists())
            d, s = l.lire(self.fichier(edition))
            d["postes"] = 500
            self.assertContains(self.deposer(l.ecrire(d, s)), "signature incorrecte")

    def test_expiree_ne_devient_pas_activation_et_historique_preserve(self):
        self.choisir_edition("transport")
        self.deposer(self.fichier("transport"))
        expiree = self.fichier("transport", valable_jusqu_au=(datetime.date.today() - datetime.timedelta(days=1)).isoformat())
        self.assertContains(self.deposer(expiree), "licence déjà expirée")
        self.assertEqual(LicenceDeposee.objects.filter(valide=True).count(), 1)
        self.assertEqual(LicenceDeposee.objects.filter(valide=False).count(), 1)
        self.assertFalse(l.etat().lecture_seule)
