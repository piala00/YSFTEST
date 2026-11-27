"""Consultation seule des exercices clôturés dans le catalogue multi-sociétés."""
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from unittest import mock

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import ResolverMatch

from .catalogue_societes import base_courante_cloturee
from .middleware import ArchiveLectureSeuleMiddleware
from .models import Exercice
from .synchronisation import verifier_saisie


class ArchiveCatalogueTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        racine = Path(self.temp.name)
        self.base = racine / "2026.sqlite3"
        self.catalogue = racine / "societes.json"
        self.configuration = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": str(self.base),
            }
        }

    def ecrire_catalogue(self, cloture=True):
        self.catalogue.write_text(json.dumps({
            "version": 1,
            "bases": [{
                "id": "n", "societe": "Transport Centrale", "agence": "Centre",
                "exercice": "2026", "moteur": "sqlite", "base": str(self.base),
                "cloture": cloture,
            }],
        }), encoding="utf-8")

    def test_base_courante_reconnait_l_archive_et_l_exercice_ouvert(self):
        self.ecrire_catalogue(True)
        with override_settings(DATABASES=self.configuration), mock.patch.dict(
            os.environ, {"ERP_CATALOGUE_SOCIETES": str(self.catalogue)}
        ):
            self.assertTrue(base_courante_cloturee())
            self.ecrire_catalogue(False)
            self.assertFalse(base_courante_cloturee())

    def test_base_sqlserver_et_catalogue_absent_ne_sont_pas_des_archives_sqlite(self):
        with override_settings(DATABASES={
            "default": {"ENGINE": "mssql", "NAME": "ERP_TRANSPORT"}
        }), mock.patch.dict(os.environ, {"ERP_CATALOGUE_SOCIETES": str(self.catalogue)}):
            self.assertFalse(base_courante_cloturee())
        with override_settings(DATABASES=self.configuration), mock.patch.dict(
            os.environ, {"ERP_CATALOGUE_SOCIETES": ""}
        ):
            self.assertFalse(base_courante_cloturee())


class ArchiveLectureSeuleMiddlewareTests(ArchiveCatalogueTests):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.middleware = ArchiveLectureSeuleMiddleware(lambda request: HttpResponse("OK"))

    def traiter(self, methode, nom_vue, cloture=True):
        self.ecrire_catalogue(cloture)
        request = getattr(self.factory, methode.lower())("/transport/billetterie/caisse/")
        request.resolver_match = ResolverMatch(lambda req: HttpResponse("OK"), (), {}, url_name=nom_vue)
        with override_settings(DATABASES=self.configuration), mock.patch.dict(
            os.environ, {"ERP_CATALOGUE_SOCIETES": str(self.catalogue)}
        ):
            return self.middleware.process_view(request, lambda req: HttpResponse("OK"), (), {})

    def test_archive_autorise_lecture_mais_refuse_toute_mutation(self):
        self.assertIsNone(self.traiter("GET", "ma_caisse_billetterie"))
        reponse = self.traiter("POST", "ma_caisse_billetterie")
        self.assertEqual(reponse.status_code, 403)
        self.assertIn("consultation seule", reponse.content.decode("utf-8"))

    def test_authentification_deconnexion_et_changement_de_dossier_restent_possibles(self):
        for nom in ("login", "logout", "choix_societe"):
            with self.subTest(nom=nom):
                self.assertIsNone(self.traiter("POST", nom))

    def test_exercice_ouvert_conserve_les_mutations(self):
        self.assertIsNone(self.traiter("POST", "ma_caisse_billetterie", cloture=False))

    def test_catalogue_invalide_refuse_les_mutations_par_securite(self):
        self.catalogue.write_text("{invalide", encoding="utf-8")
        request = self.factory.post("/transport/billetterie/caisse/")
        request.resolver_match = ResolverMatch(lambda req: HttpResponse("OK"), (), {}, url_name="ma_caisse_billetterie")
        with override_settings(DATABASES=self.configuration), mock.patch.dict(
            os.environ, {"ERP_CATALOGUE_SOCIETES": str(self.catalogue)}
        ):
            reponse = self.middleware.process_view(request, lambda req: HttpResponse("OK"), (), {})
        self.assertEqual(reponse.status_code, 503)
        self.assertIn("saisie refusée", reponse.content.decode("utf-8"))


class ArchiveServicesTests(TestCase):
    def test_verifier_saisie_refuse_une_archive(self):
        exercice = Exercice.objects.create(
            code="2026", date_debut=date(2026, 1, 1), date_fin=date(2026, 12, 31)
        )
        from django.conf import settings

        with tempfile.TemporaryDirectory() as dossier:
            catalogue = Path(dossier) / "societes.json"
            base = str(settings.DATABASES["default"]["NAME"])
            catalogue.write_text(json.dumps({
                "version": 1,
                "bases": [{
                    "id": "n", "societe": "Transport Centrale", "agence": "Centre",
                    "exercice": "2026", "moteur": "sqlite", "base": base, "cloture": True,
                }],
            }), encoding="utf-8")
            with mock.patch.dict(os.environ, {"ERP_CATALOGUE_SOCIETES": str(catalogue)}):
                with self.assertRaisesMessage(ValidationError, "consultation seule"):
                    verifier_saisie("ouvrir une caisse")
                with self.assertRaisesMessage(ValidationError, "consultation seule"):
                    Exercice.pour_date(date(2026, 6, 1))
        self.assertFalse(exercice.cloture)
