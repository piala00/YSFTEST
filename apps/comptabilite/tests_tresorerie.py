"""Trésorerie projetée : départ réel, factures à échéance, prévisions uniques et mensuelles, budget en option."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Article, Document, LigneDocument, Tiers
from apps.core.models import Exercice

from .models import Budget, Compte, Journal, LigneBudget, PrevisionTresorerie
from .services import creer_ecriture
from .tresorerie_projetee import projection

D = Decimal
AUJOURDHUI = datetime.date(2030, 1, 15)


class TresorerieProjeteeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        Exercice.objects.create(code="T2030", date_debut=datetime.date(2030, 1, 1), date_fin=datetime.date(2030, 12, 31))
        caisse = Compte.objects.get_or_create(numero="5711000", defaults={"intitule": "Caisse"})[0]
        capital = Compte.objects.get_or_create(numero="1011000", defaults={"intitule": "Capital"})[0]
        creer_ecriture(Journal.objects.get(code="OD"), datetime.date(2030, 1, 2), "Apport",
                       [{"compte": caisse, "debit": 500000}, {"compte": capital, "credit": 500000}])
        client_ = Tiers.objects.create(code="TC1", nom="Client")
        fournisseur = Tiers.objects.create(code="TF1", nom="Fournisseur", type_tiers=Tiers.FOURNISSEUR)
        article = Article.objects.create(reference="TA1", designation="Article", prix_achat=800, prix_vente=1000)
        entree = Document.objects.create(type_document=Document.STOCK_ENTREE, date=datetime.date(2030, 1, 2))
        LigneDocument.objects.create(document=entree, article=article, quantite=100, prix_unitaire=800)
        entree.recalculer()
        entree.valider()

        def facture(type_document, tiers, date, echeance, montant):
            d = Document.objects.create(type_document=type_document, tiers=tiers, date=date, date_echeance=echeance)
            LigneDocument.objects.create(document=d, article=article, quantite=1, prix_unitaire=montant)
            d.recalculer()
            d.valider()
            return d
        cls.echue = facture(Document.FACTURE, client_, datetime.date(2030, 1, 3), datetime.date(2030, 1, 10), 100000)
        cls.mars = facture(Document.FACTURE, client_, datetime.date(2030, 1, 5), datetime.date(2030, 3, 5), 200000)
        cls.fevrier = facture(Document.ACHAT_FACTURE, fournisseur, datetime.date(2030, 1, 6), datetime.date(2030, 2, 20), 50000)

    def test_projection_mois_par_mois(self):
        PrevisionTresorerie.objects.create(date=datetime.date(2030, 1, 31), libelle="Emprunt", montant=30000, mensuelle=True,
                                           jusqu_au=datetime.date(2030, 3, 31))
        PrevisionTresorerie.objects.create(date=datetime.date(2030, 2, 10), libelle="Apport", montant=70000,
                                           sens=PrevisionTresorerie.ENCAISSEMENT)
        p = projection(AUJOURDHUI, 4)
        self.assertEqual(p["depart"], D(500000))
        l = {x["debut"].month: x for x in p["lignes"]}
        self.assertEqual(l[1]["clients"], self.echue.reste_a_payer)                # échue : comptée dans le mois en cours
        self.assertEqual(l[3]["clients"], self.mars.reste_a_payer)
        self.assertEqual(l[2]["fournisseurs"], self.fevrier.reste_a_payer)
        self.assertEqual([l[m]["prevues_sorties"] for m in (1, 2, 3, 4)], [D(30000), D(30000), D(30000), 0])
        self.assertEqual(l[2]["prevues_entrees"], D(70000))
        for a, b in zip(p["lignes"], p["lignes"][1:]):                             # enchaînement des soldes
            self.assertEqual(b["solde_debut"], a["solde_fin"])
        self.assertEqual(p["fin"], D(500000) + self.echue.reste_a_payer + self.mars.reste_a_payer
                         - self.fevrier.reste_a_payer - 90000 + 70000)
        self.assertTrue(any(d["en_retard"] for d in p["detail"]))

    def test_prevision_mensuelle_en_fin_de_mois(self):
        p = PrevisionTresorerie(date=datetime.date(2030, 1, 31), libelle="Loyer", montant=1, mensuelle=True)
        self.assertEqual(p.occurrences(datetime.date(2030, 1, 1), datetime.date(2030, 4, 30)),
                         [datetime.date(2030, 1, 31), datetime.date(2030, 2, 28), datetime.date(2030, 3, 31),
                          datetime.date(2030, 4, 30)])

    def test_budget_valide_en_option(self):
        b = Budget.objects.create(exercice=Exercice.objects.get(code="T2030"), nom="Société", statut=Budget.VALIDE)
        l = LigneBudget(budget=b, compte="62")
        for m in LigneBudget.MOIS:
            setattr(l, m, 10000)
        l.save()
        p = projection(AUJOURDHUI, 3, budget=b)
        self.assertEqual([x["budget_sorties"] for x in p["lignes"]], [0, D(10000), D(10000)])   # pas le mois en cours

    def test_ecran(self):
        self.client.force_login(get_user_model().objects.create_superuser("chef", "", "Chef-2026x"))
        url = reverse("comptabilite:tresorerie_projetee")
        self.client.post(url, {"action": "ajouter", "date": "2030-02-01", "sens": "DECAISSEMENT", "montant": "25 000",
                               "libelle": "Impôt", "mensuelle": "1"})
        self.assertEqual(PrevisionTresorerie.objects.get().montant, D(25000))
        self.client.post(url, {"action": "ajouter", "date": "2030-02-01", "montant": "-5", "libelle": "x"})   # refusé
        self.assertEqual(PrevisionTresorerie.objects.count(), 1)
        page = self.client.get(url + "?seul=1&mois=12")
        self.assertContains(page, "data-graphique")
        self.assertContains(page, "Point le plus bas")
