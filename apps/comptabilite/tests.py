import datetime
import io
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


class PlanSeptChiffresTests(TestCase):
    """Plan comptable à 7 chiffres : nouveau dossier, saisie, conversion d'un dossier existant."""

    def test_nouveau_dossier_a_sept_chiffres(self):
        from apps.core.models import Societe

        call_command("init_erp", verbosity=0)
        self.assertEqual(Societe.get().longueur_comptes, 7)
        numeros = set(Compte.objects.values_list("numero", flat=True))
        self.assertTrue(all(len(n) == 7 for n in numeros), sorted(n for n in numeros if len(n) != 7))
        self.assertIn("4111000", numeros)
        # Le code et les écrans qui désignent un compte par son numéro court le retrouvent
        self.assertEqual(Compte.objects.get(numero="4111").numero, "4111000")
        self.assertEqual(Compte.par_numero("571").numero, "5710000")
        self.assertEqual(Compte.objects.get_or_create(numero="47121", defaults={"intitule": "Avances"})[0].numero, "4712100")
        self.assertEqual(Compte.objects.filter(numero__in=["101", "701"]).count(), 2)
        # Saisie : complété par des zéros ; plus de 7 chiffres refusé
        c = Compte(numero="6058", intitule="Autres achats")
        c.full_clean()
        self.assertEqual(c.numero, "6058000")
        with self.assertRaisesMessage(ValidationError, "7 chiffres"):
            Compte(numero="60580001", intitule="Trop long").full_clean()
        # Les états par préfixe restent justes (classe 4, compte 411…)
        self.assertTrue(Compte.objects.filter(numero__startswith="411").exists())

    def test_conversion_d_un_dossier_existant(self):
        from apps.core.models import Societe

        call_command("init_erp", "--longueur-comptes", "0", verbosity=0)
        self.assertEqual(Societe.get().longueur_comptes, 0)
        self.assertTrue(Compte.objects.filter(numero="4111").exists())
        exercice = Exercice.objects.first()
        e = services.creer_ecriture(Journal.objects.get(code="VT"), exercice.date_debut, "Vente",
                                    [{"compte": Compte.objects.get(numero="4111"), "debit": 1000},
                                     {"compte": Compte.objects.get(numero="701"), "credit": 1000}])
        sortie = io.StringIO()
        call_command("longueur_comptes", stdout=sortie)                      # simulation : rien ne change
        self.assertIn("compte(s) à renuméroter", sortie.getvalue())
        self.assertIn(("4111", "4111000"), services.projet_longueur_comptes(7)[0])
        self.assertTrue(Compte.objects.filter(numero="4111").exists())
        call_command("longueur_comptes", "--appliquer", stdout=io.StringIO())
        self.assertEqual(Societe.get().longueur_comptes, 7)
        self.assertEqual(sorted(e.lignes.values_list("compte__numero", flat=True)), ["4111000", "7010000"])
        self.assertEqual(sum(l.debit - l.credit for l in e.lignes.all()), 0)  # montants intacts

    def test_collision_refusee(self):
        from django.core.management.base import CommandError

        call_command("init_erp", "--longueur-comptes", "0", verbosity=0)
        Compte.objects.create(numero="4111000", intitule="Clients (déjà à 7 chiffres)")
        with self.assertRaisesMessage(CommandError, "collision"):
            call_command("longueur_comptes", "--appliquer", stdout=io.StringIO())
        self.assertTrue(Compte.objects.filter(numero="4111").exists())       # rien n'a bougé

class TestSecuriteLongueurSeptChiffres(TestCase):
    """Ne jamais rendre un plan hétérogène en autorisant des comptes > 7 chiffres."""

    def test_conversion_refuse_compte_trop_long_sans_modification(self):
        from django.core.management.base import CommandError
        from apps.core.models import Societe
        from apps.comptabilite.models import Compte
        call_command("init_erp", "--longueur-comptes", "0", verbosity=0)
        compte = Compte.objects.create(numero="41112345", intitule="Compte existant à 8 chiffres")
        with self.assertRaises(CommandError):
            call_command("longueur_comptes", "--appliquer", stdout=io.StringIO())
        compte.refresh_from_db()
        self.assertEqual(compte.numero, "41112345")
        self.assertEqual(Societe.get().longueur_comptes, 0)

    def test_ecriture_directe_refuse_un_compte_trop_long(self):
        from django.core.exceptions import ValidationError
        from apps.comptabilite.models import Compte
        call_command("init_erp", verbosity=0)
        with self.assertRaises(ValidationError):
            Compte.objects.create(numero="41112345", intitule="Dépassement interdit")


