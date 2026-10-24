"""Revue GPT du 24/10/2026 (skill erp-ohada-retour-revue-conditionnements-consolidation) : anomalies A01–A07.

Tests de reproduction fournis par la revue, conservés comme tests de non-régression. Seul A07 est adapté : un
règlement Mobile Money sur la caisse espèces est désormais refusé (au lieu d'être accepté sans effet sur la caisse).
"""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.commercial import fiche_stock
from apps.commercial import tests_fiche_stock as fs
from apps.commercial.models import Document, PointageFiche, Reglement, StockDepot
from apps.comptabilite.models import Journal
from apps.core.models import DroitAcces
from apps.reporting import services
from apps.reporting import tests_rapport_commercial as rs


class StockReview(TestCase):
    piece = fs.FicheStockTests.__dict__["piece"]

    @classmethod
    def setUpTestData(cls):
        fs.FicheStockTests.setUpTestData.__func__(cls)

    def pointer(self, quantite=None, **extra):
        donnees = {"numero": self.livraison.numero, "depot": self.depot.pk, **extra}
        if quantite is not None:
            donnees[f"qte_{self.huile.pk}"] = quantite
        return self.client.post(reverse("commercial:pointage"), donnees)

    def test_A02_vide_n_est_pas_zero(self):
        self.client.force_login(self.fichiste)
        reponse = self.pointer()
        self.assertContains(reponse, "Quantité non saisie")
        self.assertFalse(PointageFiche.objects.filter(document=self.livraison).exists())
        self.pointer("0")                                                       # zéro saisi explicitement : accepté
        ligne = PointageFiche.objects.get(document=self.livraison).lignes.get()
        self.assertEqual((ligne.quantite_saisie, ligne.ecart), (Decimal("0"), Decimal("-10")))

    def test_A03_quantite_negative_refusee(self):
        self.client.force_login(self.fichiste)
        self.assertContains(self.pointer("-5"), "Quantité incorrecte")
        self.assertFalse(PointageFiche.objects.filter(document=self.livraison).exists())
        with self.assertRaises(ValidationError):                               # contrôle aussi hors formulaire
            PointageFiche(document=self.livraison, depot=self.depot).enregistrer({self.huile.pk: Decimal("-5")})

    def test_A01_api_ne_revele_pas_les_quantites(self):
        groupe = Group.objects.create(name="Fichiste contrôle")
        self.fichiste.groups.add(groupe)
        for racine in ["fichier", "edition", "structure", "traitement", "etat"]:
            DroitAcces.objects.create(groupe=groupe, module="commercial", code=racine, niveau="INTERDIT")
        DroitAcces.objects.create(groupe=groupe, module="commercial", code="fiche_stock.pointage", niveau="TOUT")
        for logiciel in ("comptabilite", "reporting"):
            DroitAcces.objects.create(groupe=groupe, module=logiciel, code="etat", niveau="INTERDIT")
        self.client.force_login(self.fichiste)
        self.assertEqual(self.client.get("/api/documents/?type=LIVRAISON").status_code, 403)
        globale = self.client.get("/api/documents/")
        corps = globale.json() if globale.status_code == 200 else {}
        donnees = corps.get("results", []) if isinstance(corps, dict) else corps
        self.assertFalse(any(d.get("id") == self.livraison.pk for d in donnees))
        self.assertEqual(self.client.get(f"/api/documents/{self.livraison.pk}/").status_code, 404)
        for etat in ("/api/reporting/balance/", "/api/reporting/bilan/", "/api/reporting/balance-agee/"):
            self.assertEqual(self.client.get(etat).status_code, 403, etat)

    def test_A04_auteur_de_la_declaration_remplacee(self):
        p = PointageFiche(document=self.livraison, depot=self.depot, fichiste=self.fichiste,
                          cree_par=self.fichiste).enregistrer({self.huile.pk: Decimal("12")})
        second = get_user_model().objects.create_user("second-fichiste", "", "x")
        self.client.force_login(second)
        self.pointer("10", observation="Correction de lecture")
        p.refresh_from_db()
        self.assertEqual(p.historique[0]["fichiste"], self.fichiste.username)       # auteur d'origine conservé
        self.assertEqual(p.historique[0]["corrige_par"], second.username)
        self.assertEqual((p.fichiste, p.cree_par, p.revision), (second, self.fichiste, 2))

    def test_A06_fiche_sans_les_bons_non_pointes(self):
        PointageFiche(document=self.entree, depot=self.depot).enregistrer({self.huile.pk: Decimal("100")})
        f = fiche_stock.fiche_article(self.huile, self.depot, self.jour, self.jour)
        en_attente = [l for l in f["lignes"] if l["a_pointer"]]
        self.assertEqual((f["solde_fiche"], f["solde_machine"]), (Decimal("100"), Decimal("90")))
        self.assertEqual((len(en_attente), en_attente[0]["attente"], en_attente[0]["sortie"]), (1, Decimal("-10"), 0))
        self.assertEqual((f["attente"], f["solde_projete"], f["ecart"]), (Decimal("-10"), Decimal("90"), 0))
        ligne = fiche_stock.rapprochement(self.depot)[0]
        self.assertEqual((ligne["machine"], ligne["attente"], ligne["fiche"]), (Decimal("90"), Decimal("-10"), Decimal("100")))

    def test_R18_alerte_bons_non_pointes_apres_delai(self):
        PointageFiche(document=self.entree, depot=self.depot).enregistrer({self.huile.pk: Decimal("100")})
        self.assertEqual(fiche_stock.bons_en_retard(self.depot, self.jour, 1), [])           # le jour même : pas d'alerte
        apres = self.jour + datetime.timedelta(days=2)
        self.assertEqual(fiche_stock.bons_en_retard(self.depot, apres, 1), [self.livraison])  # la livraison seule
        self.assertEqual(fiche_stock.bons_en_retard(self.depot, apres, 3), [])

    def test_R13_livraison_partielle_puis_facture(self):
        commande = self.piece(Document.COMMANDE, 10, self.client_)
        livraison = commande.transformer(Document.LIVRAISON)
        ligne = livraison.lignes.get()
        ligne.quantite = 4
        ligne.save()
        livraison.recalculer()
        livraison.valider()
        facture = livraison.transformer(Document.FACTURE)
        facture.valider()
        commande.refresh_from_db()
        self.assertEqual(commande.lignes.get().reste_a_transformer, Decimal("6"))
        self.assertEqual(facture.lignes.get().quantite, Decimal("4"))
        self.assertEqual(StockDepot.quantite_de(self.huile.pk, self.depot.pk), Decimal("86"))   # pas de seconde sortie


class ReportReview(TestCase):
    piece = rs.RapportCommercialTests.piece
    regler = rs.RapportCommercialTests.regler

    @classmethod
    def setUpTestData(cls):
        rs.RapportCommercialTests.setUpTestData.__func__(cls)

    def test_A05_rapport_passe_fige_a_sa_date(self):
        hier = self.jour - datetime.timedelta(days=1)
        doc = self.piece(Document.FACTURE, 3, valider=False)
        doc.date = hier
        doc.save()
        doc.valider()
        avant = services.rapport_commercial(hier)["ventes"]["credit"]
        self.regler(3000, facture=doc, date=self.jour)
        self.assertEqual(services.rapport_commercial(hier)["ventes"]["credit"], avant)
        self.assertEqual(avant, Decimal("3000"))

    def test_A07_mobile_money_hors_caisse_especes(self):
        doc = self.piece(Document.FACTURE, 3)
        avant = services.rapport_commercial(self.jour)["solde"]["cloture"]
        with self.assertRaisesMessage(ValidationError, "ne peut pas entrer dans la caisse"):
            self.regler(3000, facture=doc, mode=Reglement.MOBILE_MONEY)
        Reglement(tiers=self.client_, journal=Journal.objects.get(code="MM"), mode=Reglement.MOBILE_MONEY,
                  montant=Decimal("3000"), facture=doc).enregistrer()
        r = services.rapport_commercial(self.jour)
        self.assertEqual(r["solde"]["cloture"], avant)                          # la caisse espèces ne bouge pas
        self.assertEqual([(t["journal__code"], t["mode"], t["total"]) for t in r["autres_tresoreries"]],
                         [("MM", Reglement.MOBILE_MONEY, Decimal("3000"))])
