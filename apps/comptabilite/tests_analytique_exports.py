"""Recette des exports XLSX analytiques sans base métier ni écritures dupliquées."""
import datetime
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.utils import timezone

from apps.core.models import Agence
from openpyxl import load_workbook

from . import plan_analytique as pa
from . import views_analytique as vues


class ExportsAnalytiquesXlsxTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)
        self.debut = datetime.date(2026, 1, 1)
        self.fin = datetime.date(2026, 1, 31)
        self.periode = {"du": self.debut, "au": self.fin, "code": "personnalisee", "erreur": ""}

    def requete(self, chemin, **params):
        request = self.factory.get(chemin, {
            "du": self.debut.isoformat(),
            "au": self.fin.isoformat(),
            "export": "xlsx",
            **params,
        })
        request.user = self.user
        return request

    def patches_periode(self):
        return (
            patch.object(pa, "lire_periode", return_value=self.periode),
            patch.object(pa, "decaler", return_value=(self.debut, self.fin)),
            patch.object(pa, "ecritures_provisoires", return_value=[]),
        )

    def test_balance_axe_exporte_totaux_et_libelles_sans_formule_excel(self):
        balance = {
            "elements": [
                {"libelle": "Web", "produits": Decimal("1200.50"), "charges": Decimal("100.00"),
                 "resultat": Decimal("1100.50"), "lignes": 3},
                {"libelle": '=HYPERLINK("https://invalid")', "produits": Decimal("10.00"),
                 "charges": Decimal("0.00"), "resultat": Decimal("10.00"), "lignes": 1},
            ],
            "non_affecte": {"produits": Decimal("0.00"), "charges": Decimal("0.00"),
                            "resultat": Decimal("0.00"), "lignes": 0},
        }
        with (
            self.patches_periode()[0] as lire_periode,
            self.patches_periode()[1] as decaler,
            self.patches_periode()[2] as provisoires,
            patch.object(pa, "titre_axe", return_value="Canaux de vente"),
            patch.object(pa, "balance_axe", return_value=balance),
        ):
            response = vues.axe(self.requete("/analytique/canaux_vente/", tri="resultat"), "canaux_vente")

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", response["Content-Type"])
        self.assertIn(".xlsx", response["Content-Disposition"])
        classeur = load_workbook(BytesIO(response.content), data_only=True)
        feuille = classeur["Analytique"]
        self.assertEqual(feuille["A1"].value, "Élément")
        self.assertEqual(feuille["A2"].value, "Web")
        self.assertEqual(feuille["B2"].value, 1200.5)
        self.assertTrue(feuille["A3"].value.startswith("'="))
        self.assertEqual(feuille["A4"].value, "Non affecté")
        self.assertEqual(feuille.freeze_panes, "A2")
        self.assertEqual(feuille.auto_filter.ref, "A1:E4")

    def test_grand_livre_exporte_toutes_les_lignes_et_conserve_la_periode(self):
        lignes = [{
            "date": datetime.date(2026, 1, 10),
            "piece": "VT-2026-001",
            "journal": "VT",
            "compte": "7061000",
            "libelle": "Vente WEB",
            "montant": Decimal("2500.00"),
        }]
        resultat = {
            "lignes": lignes,
            "comptes": [],
            "series": [],
            "croise": [],
            "comparaison": [],
            "journal": [],
            "journal_axes": [],
        }
        with (
            self.patches_periode()[0],
            self.patches_periode()[1],
            self.patches_periode()[2],
            patch.object(pa, "titre_axe", return_value="Canaux de vente"),
            patch.object(pa, "cle_depuis_url", return_value="WEB"),
            patch.object(pa, "axes", return_value=[
                ("canaux_vente", "Canaux de vente", ""),
                ("vehicules", "Véhicules", ""),
            ]),
            patch.object(pa, "etat_element", return_value=resultat) as etat_element,
            patch.object(pa, "libelles", return_value={"WEB": "Web"}),
        ):
            response = vues.element(
                self.requete("/analytique/canaux_vente/WEB/", etat="grand_livre", axe2="vehicules", comparer="n1"),
                "canaux_vente",
                "WEB",
            )

        self.assertEqual(response.status_code, 200)
        etat_element.assert_called_once_with(
            "canaux_vente", "WEB", "grand_livre", self.debut, self.fin,
            axe2="vehicules", comparer="n1",
        )
        classeur = load_workbook(BytesIO(response.content), data_only=True)
        feuille = classeur["Analytique"]
        self.assertEqual(feuille.max_row, 2)
        self.assertEqual(feuille["A2"].value, datetime.datetime(2026, 1, 10, 0, 0))
        self.assertEqual(feuille["B2"].value, "VT-2026-001")
        self.assertEqual(feuille["F2"].value, 2500)


    def test_balance_axe_exporte_pdf_multipage_avec_rapprochement(self):
        balance = {
            "elements": [
                {"libelle": f"Véhicule {i:03d}", "produits": Decimal("1200.50"), "charges": Decimal("100.00"),
                 "resultat": Decimal("1100.50"), "lignes": 3}
                for i in range(90)
            ],
            "total_elements": {"produits": Decimal("108045.00"), "charges": Decimal("9000.00"),
                               "resultat": Decimal("99045.00"), "lignes": 270},
            "non_affecte": {"produits": Decimal("0.00"), "charges": Decimal("0.00"),
                            "resultat": Decimal("0.00"), "lignes": 0},
            "gl": {"produits": Decimal("108045.00"), "charges": Decimal("9000.00"),
                   "resultat": Decimal("99045.00"), "lignes": 270},
            "rapproche": True,
        }
        with (
            self.patches_periode()[0],
            self.patches_periode()[1],
            self.patches_periode()[2],
            patch.object(pa, "titre_axe", return_value="Véhicules"),
            patch.object(pa, "balance_axe", return_value=balance),
        ):
            response = vues.axe(
                self.requete("/analytique/vehicules/", export="pdf"),
                "vehicules",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertTrue(response["Content-Disposition"].endswith(".pdf\""))
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertIn(b"%%EOF", response.content[-128:])
        self.assertGreater(len(response.content), 3000)

    def test_element_exporte_pdf_et_echappe_les_libelles_metier(self):
        resultat = {
            "lignes": [{
                "date": self.debut,
                "piece": "VT-2026-001",
                "journal": "VT",
                "compte": "7061000",
                "libelle": "<script>Vente WEB & mobile</script>",
                "montant": Decimal("2500.00"),
            }],
            "comptes": [],
            "series": [],
            "croise": [],
            "comparaison": [],
            "journal": [],
            "journal_axes": [],
        }
        with (
            self.patches_periode()[0],
            self.patches_periode()[1],
            self.patches_periode()[2],
            patch.object(pa, "titre_axe", return_value="Canaux de vente"),
            patch.object(pa, "cle_depuis_url", return_value="WEB"),
            patch.object(pa, "axes", return_value=[
                ("canaux_vente", "Canaux de vente", ""),
                ("vehicules", "Véhicules", ""),
            ]),
            patch.object(pa, "etat_element", return_value=resultat),
            patch.object(pa, "libelles", return_value={"WEB": "Web"}),
        ):
            response = vues.element(
                self.requete("/analytique/canaux_vente/WEB/", etat="grand_livre", export="pdf"),
                "canaux_vente",
                "WEB",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertIn(b"%%EOF", response.content[-128:])


class FraicheurAgencesAnalytiquesTests(TestCase):
    """La direction voit la date réelle des derniers lots reçus, sans la confondre avec une présence réseau."""

    @staticmethod
    def rendre_indicateur():
        return Template("{% load fraicheur %}{% fraicheur_agences %}").render(Context({}))

    def test_siege_affiche_la_reception_et_la_sequence_de_chaque_agence_active(self):
        from datetime import timedelta

        recue = timezone.now() - timedelta(hours=2)
        Agence.objects.create(
            code="SIEGE", nom="Direction", locale=True, role=Agence.SIEGE,
        )
        # bulk_create évite volontairement la création automatique des comptes de liaison :
        # cette recette porte sur la lecture des métadonnées de synchronisation.
        Agence.objects.bulk_create([
            Agence(code="DLA", nom="Douala", role=Agence.AGENCE,
                   derniere_reception=recue, sequence_integree=42),
            Agence(code="BTA", nom="Bertoua", role=Agence.AGENCE,
                   derniere_reception=None, sequence_integree=0),
            Agence(code="OLD", nom="Agence inactive", role=Agence.AGENCE, actif=False),
        ])

        html = self.rendre_indicateur()

        self.assertIn("Fraîcheur des données reçues des agences", html)
        self.assertIn("Douala", html)
        self.assertIn("DLA", html)
        self.assertIn("Dernier lot reçu", html)
        self.assertIn("il y a", html)
        self.assertIn("Séquence intégrée : 42", html)
        self.assertIn("Bertoua", html)
        self.assertIn("Aucun lot reçu enregistré", html)
        self.assertNotIn("Agence inactive", html)
        self.assertIn("ne constitue pas une mesure de connexion réseau", html)

    def test_une_agence_locale_ne_recoit_pas_le_bandeau_de_consolidation(self):
        Agence.objects.create(
            code="DLA", nom="Douala", locale=True, role=Agence.AGENCE,
        )
        Agence.objects.bulk_create([
            Agence(code="BTA", nom="Bertoua", role=Agence.AGENCE,
                   derniere_reception=timezone.now(), sequence_integree=12),
        ])

        html = self.rendre_indicateur()

        self.assertNotIn("Fraîcheur des données reçues des agences", html)
        self.assertNotIn("Bertoua", html)


    def test_bandeau_ne_recharge_pas_les_agences_dans_la_meme_requete(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        Agence.objects.create(
            code="SIEGE", nom="Direction", locale=True, role=Agence.SIEGE,
        )
        Agence.objects.bulk_create([
            Agence(code="DLA", nom="Douala", role=Agence.AGENCE,
                   derniere_reception=timezone.now(), sequence_integree=42),
        ])
        modele = Template(
            "{% load fraicheur %}{% fraicheur_agences %}{% fraicheur_agences %}"
        )
        requete = RequestFactory().get("/analytique/")

        with CaptureQueriesContext(connection) as requetes:
            html = modele.render(Context({"request": requete}))

        self.assertEqual(len(requetes), 1)
        self.assertEqual(html.count("Douala"), 2)
        self.assertEqual(html.count("Séquence intégrée : 42"), 2)

        # Le cache ne dépasse pas la requête : le prochain écran voit la nouvelle réception.
        Agence.objects.filter(code="DLA").update(sequence_integree=43)
        nouvel_html = modele.render(Context({"request": RequestFactory().get("/analytique/")}))
        self.assertIn("Séquence intégrée : 43", nouvel_html)
