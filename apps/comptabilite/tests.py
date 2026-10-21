import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from apps.core.models import Exercice

from . import etats, services
from .models import Compte, Journal


class ComptabiliteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.exercice = Exercice.objects.first()
        cls.date = cls.exercice.date_debut + datetime.timedelta(days=10)

    def ecrire(self, lignes, journal="OD"):
        return services.creer_ecriture(
            Journal.objects.get(code=journal), self.date, "Test",
            [{"compte": Compte.objects.get(numero=n), "debit": d, "credit": c} for n, d, c in lignes],
        )

    def test_plan_syscohada_charge(self):
        for numero in ("101", "4111", "4011", "4431", "4452", "521", "571", "601", "701"):
            self.assertTrue(Compte.objects.filter(numero=numero).exists(), numero)

    def test_ecriture_desequilibree_refusee(self):
        with self.assertRaises(ValidationError):
            self.ecrire([("5711", 1000, 0), ("101", 0, 900)])

    def test_bilan_equilibre_et_resultat(self):
        self.ecrire([("5211", 1_000_000, 0), ("101", 0, 1_000_000)])           # apport en capital
        self.ecrire([("2442", 300_000, 0), ("5211", 0, 300_000)])               # achat ordinateur
        self.ecrire([("601", 200_000, 0), ("4011", 0, 200_000)], journal="AC")  # achats
        self.ecrire([("4111", 500_000, 0), ("701", 0, 500_000)], journal="VT")  # ventes
        self.ecrire([("681", 50_000, 0), ("2844", 0, 50_000)])                  # dotation
        bilan = etats.bilan(self.exercice.date_fin)
        self.assertTrue(bilan["equilibre"])
        self.assertEqual(bilan["resultat"], Decimal("250000"))
        actif = {l["ref"]: l for l in bilan["actif"]}
        self.assertEqual(actif["AI"]["brut"], Decimal("300000"))
        self.assertEqual(actif["AI"]["amort"], Decimal("50000"))
        cr = etats.compte_de_resultat(self.exercice.date_debut, self.exercice.date_fin)
        v = cr["valeurs"]
        self.assertEqual(v["XA"], Decimal("300000"))
        self.assertEqual(v["XE"], Decimal("250000"))
        self.assertEqual(v["XI"], Decimal("250000"))

    def test_banque_crediteur_au_passif(self):
        self.ecrire([("601", 100_000, 0), ("5211", 0, 100_000)])
        bilan = etats.bilan(self.exercice.date_fin)
        passif = {l["ref"]: l["montant"] for l in bilan["passif"]}
        self.assertEqual(passif["DR"], Decimal("100000"))
        self.assertTrue(bilan["equilibre"])

    def test_balance_equilibree(self):
        self.ecrire([("5711", 1000, 0), ("101", 0, 1000)])
        _, totaux = services.balance(self.exercice.date_debut, self.exercice.date_fin)
        self.assertEqual(totaux["mvt_d"], totaux["mvt_c"])
        self.assertEqual(totaux["solde_d"], totaux["solde_c"])

    def test_lettrage(self):
        e1 = self.ecrire([("4111", 1000, 0), ("701", 0, 1000)])
        e2 = self.ecrire([("5711", 1000, 0), ("4111", 0, 1000)])
        lignes = [e1.lignes.get(compte__numero="4111"), e2.lignes.get(compte__numero="4111")]
        self.assertEqual(services.lettrer(lignes), "A")

    def test_exercice_cloture(self):
        Exercice.objects.update(cloture=True)
        with self.assertRaises(ValidationError):
            self.ecrire([("5711", 1000, 0), ("101", 0, 1000)])
