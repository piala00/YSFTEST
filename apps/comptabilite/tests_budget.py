"""Budgets et état budget / réel (société entière et par élément d'un plan analytique)."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.models import Exercice

from . import budget as service
from .models import Budget, Compte, Journal, LigneBudget
from .services import creer_ecriture

D = Decimal


class BudgetReelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.ex = Exercice.objects.create(code="B2030", date_debut=datetime.date(2030, 1, 1), date_fin=datetime.date(2030, 12, 31))
        cls.ex_prec = Exercice.objects.create(code="B2029", date_debut=datetime.date(2029, 1, 1),
                                              date_fin=datetime.date(2029, 12, 31))
        c = {n: Compte.objects.get_or_create(numero=n, defaults={"intitule": n})[0]
             for n in ("6222000", "6011000", "7061100", "5711000")}
        cls.c = c
        from apps.transport.models import Vehicule

        cls.car = Vehicule.objects.create(immatriculation="BU 001 AA", nombre_places=30)
        od = Journal.objects.get(code="OD")

        def piece(date, compte, montant, vehicule=None, produit=False):
            ligne = {"compte": c[compte], "vehicule": vehicule, ("credit" if produit else "debit"): montant}
            creer_ecriture(od, date, f"{compte} {date}", [ligne, {"compte": c["5711000"],
                                                                  ("debit" if produit else "credit"): montant}])
        piece(datetime.date(2030, 1, 10), "6222000", 900)                       # loyer de janvier
        piece(datetime.date(2030, 1, 15), "7061100", 6000, cls.car, produit=True)
        piece(datetime.date(2030, 1, 20), "6011000", 400)                       # non budgété → hors budget
        piece(datetime.date(2030, 2, 10), "6222000", 1100)
        piece(datetime.date(2029, 3, 5), "6222000", 1000)                       # réel N-1 pour le préremplissage
        piece(datetime.date(2029, 3, 6), "7061100", 5000, cls.car, produit=True)

    def ligne(self, b, compte, annuel, element=""):
        l = LigneBudget(budget=b, element=element, compte=compte)
        for nom, v in zip(LigneBudget.MOIS, service.repartir(annuel)):
            setattr(l, nom, v)
        l.save()
        return l

    def test_repartition_au_franc_pres(self):
        mois = service.repartir(D("100000"))
        self.assertEqual(sum(mois), D("100000"))
        self.assertEqual(len(mois), 12)

    def test_budget_societe_ecarts_et_hors_budget(self):
        b = Budget.objects.create(exercice=self.ex, nom="Société")
        self.ligne(b, "62", 12000)
        self.ligne(b, "70", 60000)
        r = service.rapport(b, datetime.date(2030, 1, 1), datetime.date(2030, 1, 31))
        lignes = {l["compte"]: l for l in r["lignes"]}
        self.assertEqual((lignes["62"]["budget"], lignes["62"]["reel"], lignes["62"]["ecart"]), (D(1000), D(900), D(-100)))
        self.assertTrue(lignes["62"]["favorable"])                               # charge sous le budget
        self.assertEqual((lignes["70"]["budget"], lignes["70"]["reel"], lignes["70"]["taux"]), (D(5000), D(6000), 120))
        self.assertTrue(lignes["70"]["favorable"])
        self.assertEqual([(h["compte"], h["reel"]) for h in r["hors_budget"]], [("60", D(400))])
        # Résultat réel = produits − charges, y compris le hors budget (= la comptabilité générale)
        self.assertEqual(r["total"]["reel_resultat"], D(6000 - 900 - 400))
        self.assertEqual(r["total"]["budget_resultat"], D(4000))
        r2 = service.rapport(b, datetime.date(2030, 1, 1), datetime.date(2030, 2, 28))
        self.assertEqual({l["compte"]: l["reel"] for l in r2["lignes"]}["62"], D(2000))

    def test_recoupement_refuse(self):
        b = Budget.objects.create(exercice=self.ex, nom="Recoupement")
        self.ligne(b, "62", 1000)
        for compte in ("6222000", "6", "41", "abc"):
            with self.subTest(compte=compte), self.assertRaises(ValidationError):
                service.verifier_ligne(b, "", compte)
        self.assertEqual(service.verifier_ligne(b, "", "6011000"), "6011000")

    def test_budget_par_vehicule_et_preremplissage(self):
        b = Budget.objects.create(exercice=self.ex, nom="Véhicules", axe="vehicules")
        cree = service.preremplir(b, self.ex_prec, 10)
        self.assertEqual(cree, 1)                                                # seul le produit est rattaché au car
        l = b.lignes.get()
        self.assertEqual((l.element, l.compte, l.m03, l.total), (str(self.car.pk), "70", D(5500), D(5500)))
        self.assertEqual(service.preremplir(b, self.ex_prec), 0)                 # rien n'est recréé
        r = service.rapport(b, datetime.date(2030, 1, 1), datetime.date(2030, 3, 31))
        g = {g["element"]: g for g in r["elements"]}
        self.assertEqual((g[str(self.car.pk)]["budget_produits"], g[str(self.car.pk)]["reel_produits"]), (D(5500), D(6000)))
        self.assertIn("BU 001 AA", g[str(self.car.pk)]["element_nom"])
        self.assertEqual(g[""]["reel_charges"], D(2400))                          # charges sans véhicule : non affecté

    def test_ecrans(self):
        self.client.force_login(get_user_model().objects.create_superuser("chef", "", "Chef-2026x"))
        r = self.client.post(reverse("analytique:budgets"), {"nom": "Budget 2030", "exercice": self.ex.pk, "axe": ""})
        b = Budget.objects.get(nom="Budget 2030")
        self.assertRedirects(r, reverse("analytique:budget", args=[b.pk]), fetch_redirect_response=False)
        url = reverse("analytique:budget", args=[b.pk])
        self.client.post(url, {"action": "ajouter", "compte": "62", "repartition": "annuel", "annuel": "12 000"})
        self.client.post(url, {"action": "ajouter", "compte": "6222000", "repartition": "annuel", "annuel": "5"})  # refusé
        self.client.post(url, {"action": "ajouter", "compte": "70", "repartition": "mois", "m01": "5000", "m02": "5000"})
        self.assertEqual(sorted((l.compte, l.total) for l in b.lignes.all()), [("62", D(12000)), ("70", D(10000))])
        self.assertContains(self.client.get(url + "?seul=1"), "Préremplir")
        page = self.client.get(reverse("analytique:budget_reel", args=[b.pk]) + "?seul=1&du=2030-01-01&au=2030-01-31")
        self.assertContains(page, "data-graphique")
        self.assertContains(page, "Hors budget")
        self.client.post(url, {"action": "valider"})
        self.client.post(url, {"action": "ajouter", "compte": "60", "repartition": "annuel", "annuel": "1"})
        self.assertEqual(b.lignes.count(), 2)                                    # validé : plus de modification
        csv = self.client.get(reverse("analytique:budget_reel", args=[b.pk]) + "?du=2030-01-01&au=2030-01-31&export=csv")
        self.assertIn("Hors budget", csv.content.decode("utf-8"))
