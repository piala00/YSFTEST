"""Fiche de stock numérique : pointage à l'aveugle des bons par le fichiste et rapprochement immédiat."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.commercial import fiche_stock
from apps.commercial.models import Article, Depot, Document, LigneDocument, PointageFiche, Tiers


class FicheStockTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0, regime_tva="manuelle")
        cls.depot = Depot.par_defaut()
        cls.huile = Article.objects.create(reference="HUILE15", designation="Huile carton 15 L", prix_vente=15000)
        cls.client_ = Tiers.objects.create(code="CFS", nom="Client fiche")
        cls.entree = cls.piece(Document.STOCK_ENTREE, 100, tiers=None)
        cls.livraison = cls.piece(Document.LIVRAISON, 10, tiers=cls.client_)
        cls.jour = datetime.date.today()
        cls.fichiste = get_user_model().objects.create_user("fichiste", "", "x")

    @classmethod
    def piece(cls, type_document, quantite, tiers):
        doc = Document.objects.create(type_document=type_document, tiers=tiers, depot=cls.depot)
        LigneDocument.objects.create(document=doc, article=cls.huile, quantite=quantite, prix_unitaire=10000, taux_tva=0)
        doc.recalculer()
        doc.valider()
        return doc

    def test_pointage_conforme_et_ecart(self):
        ok = PointageFiche(document=self.entree, depot=self.depot).enregistrer({self.huile.pk: Decimal("100")})
        self.assertEqual(ok.statut, PointageFiche.CONFORME)
        ko = PointageFiche(document=self.livraison, depot=self.depot).enregistrer({self.huile.pk: Decimal("12")})
        self.assertEqual(ko.statut, PointageFiche.ECART)
        self.assertEqual(ko.lignes.get().ecart, Decimal("2"))
        # Sortie notée 12 au lieu de 10 : la fiche a 2 de moins que l'ordinateur
        ligne = fiche_stock.rapprochement(self.depot)[0]
        self.assertEqual((ligne["machine"], ligne["ecart"], ligne["fiche"]), (Decimal("90"), Decimal("-2"), Decimal("88")))
        fiche = fiche_stock.fiche_article(self.huile, self.depot, self.jour - datetime.timedelta(days=1), self.jour)
        self.assertEqual((fiche["solde_fiche"], fiche["solde_machine"]), (Decimal("88"), Decimal("90")))
        self.assertEqual(fiche_stock.ecarts(self.depot, self.jour, self.jour)[0].ecart, Decimal("2"))

    def test_bons_a_pointer(self):
        a_pointer = fiche_stock.bons_a_pointer(self.depot, self.jour, self.jour)
        self.assertEqual(set(a_pointer), {self.entree, self.livraison})
        PointageFiche(document=self.entree, depot=self.depot).enregistrer({self.huile.pk: Decimal("100")})
        self.assertEqual(list(fiche_stock.bons_a_pointer(self.depot, self.jour, self.jour)), [self.livraison])

    def test_saisie_a_l_aveugle_par_le_fichiste(self):
        self.client.force_login(self.fichiste)
        numero_court = self.livraison.numero.split("-")[-1]
        ambigu = self.client.get(reverse("commercial:pointage") + f"?numero={numero_court}")    # ME…-00001 et BL…-00001
        self.assertContains(ambigu, "Plusieurs bons se terminent par")
        page = self.client.get(reverse("commercial:pointage") + f"?numero={self.livraison.numero.lower()}&depot={self.depot.pk}")
        self.assertContains(page, "Huile carton 15 L")
        self.assertNotContains(page, 'value="10')                                 # quantité de l'ordinateur cachée
        reponse = self.client.post(reverse("commercial:pointage"), {"numero": self.livraison.numero, "depot": self.depot.pk,
                                                                     f"qte_{self.huile.pk}": "10"})
        pointage = PointageFiche.objects.get(document=self.livraison)
        self.assertRedirects(reponse, reverse("commercial:pointage_detail", args=[pointage.pk]))
        detail = self.client.get(reverse("commercial:pointage_detail", args=[pointage.pk]))
        self.assertContains(detail, "Conforme")
        self.assertNotContains(detail, "Ordinateur")                              # le fichiste ne voit pas les quantités
        self.assertEqual(pointage.fichiste, self.fichiste)
        inconnu = self.client.get(reverse("commercial:pointage") + "?numero=XX999")
        self.assertContains(inconnu, "Aucun bon ne porte le numéro")

    def test_etats(self):
        self.client.force_login(get_user_model().objects.create_superuser("chef", "", "x"))
        self.assertContains(self.client.get(reverse("commercial:fiche_rapprochement") + "?ok=1"), "Bons à pointer (2)")
        page = self.client.get(reverse("commercial:fiche_article") + f"?ok=1&article={self.huile.pk}&depot={self.depot.pk}")
        self.assertContains(page, "Stock de la fiche")
