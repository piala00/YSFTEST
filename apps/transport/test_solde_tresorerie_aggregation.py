"""Régression du solde de trésorerie après agrégation SQL (SQLite et SQL Server)."""
import datetime
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from apps.comptabilite.models import Journal
from apps.comptabilite.services import creer_ecriture
from apps.transport.models_caisse import solde_tresorerie


class SoldeTresorerieAggregationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.journal = Journal.objects.get(code="CA")
        cls.compte = cls.journal.compte_tresorerie

    def test_solde_agrege_respecte_la_date_et_les_deux_sens(self):
        from apps.comptabilite.models import Compte

        contrepartie, _ = Compte.objects.get_or_create(
            numero="471899", defaults={"intitule": "Contrepartie test trésorerie"}
        )
        jour = datetime.date(2026, 1, 10)
        lendemain = jour + datetime.timedelta(days=1)
        solde_initial = solde_tresorerie(self.compte, jour - datetime.timedelta(days=1))
        creer_ecriture(
            self.journal, jour, "Entrée test agrégation",
            [{"compte": self.compte, "debit": Decimal("15000")},
             {"compte": contrepartie, "credit": Decimal("15000")}],
        )
        creer_ecriture(
            self.journal, jour, "Sortie test agrégation",
            [{"compte": contrepartie, "debit": Decimal("4000")},
             {"compte": self.compte, "credit": Decimal("4000")}],
        )
        creer_ecriture(
            self.journal, lendemain, "Entrée future test agrégation",
            [{"compte": self.compte, "debit": Decimal("2000")},
             {"compte": contrepartie, "credit": Decimal("2000")}],
        )
        self.assertEqual(solde_tresorerie(self.compte, jour - datetime.timedelta(days=1)), solde_initial)
        self.assertEqual(solde_tresorerie(self.compte, jour), solde_initial + Decimal("11000"))
        self.assertEqual(solde_tresorerie(self.compte, lendemain), solde_initial + Decimal("13000"))
