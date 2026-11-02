"""Écran de comptabilisation (mise à jour comptable) façon Sage : le brouillard
passe en définitif par lots, avec progression et report des anomalies."""
import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.models import Exercice

from .models import Compte, Ecriture, Journal, LigneEcriture


class ComptabilisationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.exercice = Exercice.objects.first()
        cls.date = cls.exercice.date_debut + datetime.timedelta(days=5)
        cls.admin = get_user_model().objects.create_superuser("maj", "", "Essai-fictif-2026")

    def piece(self, lignes, numero):
        e = Ecriture.objects.create(journal=Journal.objects.get(code="OD"), exercice=self.exercice,
                                    numero=numero, date=self.date, libelle="Pièce fictive")
        for compte, debit, credit in lignes:
            LigneEcriture.objects.create(ecriture=e, compte=Compte.objects.get(numero=compte), debit=debit, credit=credit)
        return e

    def setUp(self):
        self.client.force_login(self.admin)

    def test_page_liste_le_brouillard(self):
        self.piece([("5711", 1000, 0), ("101", 0, 1000)], "MAJ-1")
        page = self.client.get(reverse("comptabilite:comptabilisation"))
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context["total"], 1)

    def test_lot_valide_les_pieces_equilibrees(self):
        e = self.piece([("5711", 1000, 0), ("101", 0, 1000)], "MAJ-2")
        rep = self.client.post(reverse("comptabilite:comptabiliser_lot"), {"ids[]": [e.pk]})
        self.assertEqual(rep.status_code, 200)
        data = rep.json()
        self.assertEqual(data["faits"], [e.pk])
        self.assertEqual(data["erreurs"], [])
        e.refresh_from_db()
        self.assertEqual(e.statut, Ecriture.STATUT_VALIDEE)

    def test_lot_signale_les_anomalies_sans_bloquer(self):
        bonne = self.piece([("5711", 1000, 0), ("101", 0, 1000)], "MAJ-3")
        mauvaise = self.piece([("5711", 1000, 0), ("101", 0, 800)], "MAJ-4")  # déséquilibrée
        rep = self.client.post(reverse("comptabilite:comptabiliser_lot"), {"ids[]": [bonne.pk, mauvaise.pk]})
        data = rep.json()
        self.assertEqual(data["faits"], [bonne.pk])
        self.assertEqual(len(data["erreurs"]), 1)
        self.assertEqual(data["erreurs"][0]["numero"], "MAJ-4")
        bonne.refresh_from_db(); mauvaise.refresh_from_db()
        self.assertEqual(bonne.statut, Ecriture.STATUT_VALIDEE)
        self.assertEqual(mauvaise.statut, Ecriture.STATUT_BROUILLARD)
