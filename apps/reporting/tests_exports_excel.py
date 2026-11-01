"""Recettes des fichiers réellement renvoyés par les vues, sur données fictives."""
import csv
import datetime
from decimal import Decimal
from io import BytesIO, StringIO
from urllib.parse import parse_qs, urlencode, urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from openpyxl import load_workbook

from apps.comptabilite.models import Ecriture, Journal
from apps.comptabilite.services import creer_ecriture
from apps.core.models import DroitAcces, Exercice
from apps.transport.models import Colis, Gare, ParametresTransport, Vehicule

from .exports import TYPE_XLSX, exporter_excel


ETATS = ("evolution", "comparaison", "matrice", "classement", "transport_billetterie",
         "transport_colis", "transport_colis_non_livres")


class FichierExcelTests(SimpleTestCase):
    def test_types_texte_literal_et_criteres_sans_formules(self):
        r = exporter_excel("fictif", ["Nom", "Téléphone", "Montant", "Date", "Vide", "Actif"], [
            ['=HYPERLINK("https://example.invalid")', "00699887766", Decimal("123456789.25"),
             datetime.date(2026, 9, 1), None, True],
            ["+nom\x00", "-texte", Decimal("-125.50"), None, "@texte", False]],
            [("Recherche", "=2+2")])
        wb = load_workbook(BytesIO(r.content), data_only=False)
        page = wb["Données"]
        self.assertEqual(page["A2"].data_type, "s")
        self.assertEqual(page["A2"].value, '=HYPERLINK("https://example.invalid")')
        self.assertEqual(page["B2"].value, "00699887766")
        self.assertEqual(Decimal(str(page["C2"].value)), Decimal("123456789.25"))
        self.assertEqual(page["D2"].value.date(), datetime.date(2026, 9, 1))
        self.assertIsNone(page["E2"].value)
        self.assertTrue(page["F2"].value)
        self.assertEqual(page["A3"].value, "+nom")
        self.assertEqual(page["C3"].value, -125.5)
        self.assertEqual(page.freeze_panes, "A2")
        self.assertEqual(page.auto_filter.ref, "A1:F3")
        self.assertEqual(wb["Critères"]["B2"].value, "=2+2")
        self.assertFalse(any(c.data_type == "f" for p in wb for row in p for c in row))
        wb.close()


class ExportsReportingExcelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", activite="transport", verbosity=0)
        cls.user = get_user_model().objects.create_superuser("excel-fictif", "", "Fictif-2026")
        cls.du = Exercice.objects.first().date_debut + datetime.timedelta(days=10)
        cls.au = cls.du + datetime.timedelta(days=20)
        cls.gare = Gare.objects.create(code="XL-A", nom="Gare fictive é&Ω")
        cls.arrivee = Gare.objects.create(code="XL-B", nom="Arrivée fictive")
        cls.car = Vehicule.objects.create(immatriculation="EXCEL-FICTIF", nombre_places=30)
        caisse = Journal.objects.get(code="CA")
        compte = ParametresTransport.get().compte_billets
        for montant, valider in ((5000, True), (3000, False)):
            creer_ecriture(caisse, cls.du, "Écriture fictive Excel", [
                {"compte": caisse.compte_tresorerie, "debit": montant},
                {"compte": compte, "credit": montant, "vehicule": cls.car}], valider=valider)
        cls.colis = Colis.objects.create(numero="XL-001", date=cls.au-datetime.timedelta(days=10),
            gare_depart=cls.gare, gare_arrivee=cls.arrivee, expediteur="Expéditeur fictif",
            destinataire="=2+2", tel_destinataire="00699887766", nombre=2, statut=Colis.ARRIVE)

    def setUp(self):
        self.client.force_login(self.user)
        self.params = {"du": self.du.isoformat(), "au": self.au.isoformat()}

    def classeur(self, etat, **params):
        r = self.client.get(reverse("reporting:"+etat), {**self.params, **params, "export": "xlsx"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], TYPE_XLSX)
        self.assertTrue(r["Content-Disposition"].endswith('.xlsx"'))
        wb = load_workbook(BytesIO(r.content), data_only=False)
        self.addCleanup(wb.close)
        self.assertEqual(wb.sheetnames, ["Données", "Critères"])
        return wb

    def test_les_sept_exports_excel_restituent_les_donnees_csv_sans_ecriture(self):
        n = Ecriture.objects.count()
        for etat in ETATS:
            with self.subTest(etat=etat):
                wb = self.classeur(etat)
                csv_r = self.client.get(reverse("reporting:"+etat), {**self.params, "export": "csv"})
                self.assertEqual(csv_r.status_code, 200)
                texte = list(csv.reader(StringIO(csv_r.content.decode("utf-8-sig")), delimiter=";"))
                excel = list(wb["Données"].values)
                self.assertEqual(len(excel), len(texte))
                for a, b in zip(excel, texte):
                    self.assertEqual(len(a), len(b))
                    for v, attendu in zip(a, b):
                        if isinstance(v, (int, float)):
                            self.assertEqual(Decimal(str(v)), Decimal(attendu))
                        elif isinstance(v, datetime.datetime):
                            self.assertEqual(v.date().isoformat(), attendu)
                        else:
                            self.assertEqual(v if v is not None else "", attendu)
        self.assertEqual(Ecriture.objects.count(), n)

    def test_bouton_conserve_dates_seuil_et_parametres_repetes(self):
        url = reverse("reporting:transport_colis_non_livres") + "?" + urlencode([
            *self.params.items(), ("seuil", "4"), ("tag", "a&b"), ("tag", "é")])
        page = self.client.get(url)
        self.assertContains(page, "Exporter Excel")
        lien = page.context["excel_url"]
        q = parse_qs(urlsplit(lien).query)
        self.assertEqual(q["tag"], ["a&b", "é"])
        self.assertEqual(q["seuil"], ["4"])
        self.assertEqual(q["du"], [self.du.isoformat()])
        r = self.client.get(lien)
        wb = load_workbook(BytesIO(r.content))
        self.addCleanup(wb.close)
        criteres = list(wb["Critères"].values)
        self.assertIn(("tag", "a&b"), criteres)
        self.assertIn(("tag", "é"), criteres)
        self.assertIn(("seuil", "4"), criteres)
        for etat in ("catalogue", "transport_tableau_de_bord"):
            self.assertNotContains(self.client.get(reverse("reporting:"+etat)), "Exporter Excel")

    def test_colis_dates_telephone_et_destination_restent_des_donnees(self):
        wb = self.classeur("transport_colis_non_livres", seuil="4")
        p = wb["Données"]
        self.assertEqual(p["A2"].value, "XL-001")
        self.assertEqual(p["B2"].value.date(), self.colis.date)
        self.assertEqual(p["C2"].value, 10)
        self.assertEqual(p["F2"].value, "=2+2")
        self.assertEqual(p["F2"].data_type, "s")
        self.assertEqual(p["G2"].value, "00699887766")
        self.assertEqual(p["J2"].value, "oui")

    def test_evolution_exclut_le_brouillard_et_conserve_les_nombres(self):
        p = self.classeur("evolution")["Données"]
        self.assertEqual(sum(row[1].value for row in list(p.rows)[1:]), 5000)
        self.assertEqual(p["B2"].data_type, "n")

    def test_export_vide_garde_les_entetes_et_les_criteres(self):
        Colis.objects.all().delete()
        wb = self.classeur("transport_colis_non_livres")
        self.assertEqual(wb["Données"].max_row, 1)
        self.assertEqual(wb["Données"]["A1"].value, "N° colis")
        self.assertIn(("seuil", "7"), list(wb["Critères"].values))

    def test_droits_lecture_refus_et_connexion_appliques_aux_exports(self):
        g = Group.objects.create(name="Lecture Excel fictive")
        user = get_user_model().objects.create_user("lecteur-excel", password="Fictif-2026")
        user.groups.add(g)
        self.client.force_login(user)
        droit = DroitAcces.objects.create(groupe=g, module="reporting", code="etat", niveau="LECTURE")
        for etat in ETATS:
            with self.subTest(etat=etat, droit="LECTURE"):
                self.classeur(etat)
        droit.niveau = "INTERDIT"
        droit.save()
        for etat in ETATS:
            with self.subTest(etat=etat, droit="INTERDIT"):
                self.assertEqual(self.client.get(reverse("reporting:"+etat),
                    {**self.params, "export": "xlsx"}).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("reporting:evolution"), {"export": "xlsx"}).status_code, 302)

    def test_criteres_effectifs_et_deux_periodes_sont_conserves(self):
        wb = self.classeur("comparaison", axe="vehicules", comparer="libre",
                           du_b=self.du.isoformat(), au_b=self.du.isoformat())
        criteres = dict(list(wb["Critères"].values)[1:])
        self.assertEqual(criteres["du_b"], self.du.isoformat())
        self.assertEqual(criteres["au_b"], self.du.isoformat())
        wb = self.classeur("classement", nombre="invalide", critere="invalide")
        criteres = dict(list(wb["Critères"].values)[1:])
        self.assertEqual((criteres["nombre"], criteres["critere"]), ("10", "resultat"))
        wb = self.classeur("comparaison", comparer="invalide")
        self.assertIn(("comparer", "precedente"), list(wb["Critères"].values))
        wb = self.classeur("transport_colis", axe="arrivee")
        self.assertEqual(wb["Données"]["A2"].value, self.arrivee.nom)
        self.assertIn(("axe", "arrivee"), list(wb["Critères"].values))
