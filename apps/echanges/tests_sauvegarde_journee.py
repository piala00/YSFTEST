"""F-BKP-03 : sauvegarde de fin de journée d'une agence, déposée chiffrée pour la
direction (Import/Export) puis récupérée et déchiffrée côté siège pour archivage."""
import datetime
import os
import secrets
import tempfile
import uuid
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.core import sauvegarde as _sauvegarde
from apps.core.models import Agence

from . import sauvegarde_journee as svc
from .models import SauvegardeJournaliere


class SauvegardeJourneeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        Agence.objects.update(locale=False)
        cls.ag = Agence.objects.create(code="AG1", nom="Agence Un", locale=True, role=Agence.AGENCE,
                                       uid=uuid.uuid4(), rang=2, cle_echange=secrets.token_hex(32))
        cls.siege = Agence.objects.create(code="DIR", nom="Direction", locale=False, role=Agence.SIEGE,
                                          uid=uuid.uuid4(), rang=1, cle_echange=secrets.token_hex(32))
        cls.user = get_user_model().objects.create_superuser("adminbkp", "", "x")

    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"ECHANGES_DOSSIER_PARTAGE": self.dossier}, clear=False)
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_remise_depose_le_fichier_chiffre_pour_la_direction(self):
        enreg, texte, nom = svc.remettre(self.user)
        self.assertEqual(enreg.moyen, SauvegardeJournaliere.BOITE)
        self.assertEqual(enreg.destination_code, "DIR")
        self.assertEqual(enreg.site_code, "AG1")
        depose = Path(self.dossier) / "DIR" / f"sauvegarde-AG1-{datetime.date.today():%Y%m%d}.sauvegarde.chiffre"
        self.assertTrue(depose.exists())
        # Le fichier déposé est chiffré (pas le JSON en clair).
        self.assertNotIn(b"erp-ohada-sauvegarde", depose.read_bytes()[:200])

    def test_direction_recupere_et_dechiffre(self):
        svc.remettre(self.user)
        # On se place côté direction (ce poste devient le siège).
        Agence.objects.filter(pk=self.ag.pk).update(locale=False)
        Agence.objects.filter(pk=self.siege.pk).update(locale=True)
        recues = svc.recues()
        self.assertEqual(len(recues), 1)
        self.assertEqual(recues[0]["agence_code"], "AG1")
        texte, nom = svc.recuperer(recues[0]["nom"], self.user)
        self.assertTrue(nom.endswith(".json"))
        _sauvegarde.lire(texte)  # le contenu déchiffré est une sauvegarde valide (sinon lève)

    def test_sans_boite_la_sauvegarde_est_a_telecharger(self):
        self.env.stop()  # plus de boîte configurée
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ECHANGES_DOSSIER_PARTAGE", None)
            enreg, texte, nom = svc.remettre(self.user)
        self.env.start()  # pour le tearDown
        self.assertEqual(enreg.moyen, SauvegardeJournaliere.TELECHARGEMENT)
        self.assertTrue(nom.endswith(".json"))
