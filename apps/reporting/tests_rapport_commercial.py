"""Rapport commercial journalier : ventes, encaissements, hors recettes, sorties, solde de caisse ; acomptes sur commande."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Article, Document, LigneDocument, OperationCaisse, Reglement, Tiers
from apps.comptabilite.models import Compte, Journal
from apps.core.models import Agence
from apps.reporting import services


class RapportCommercialTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0, regime_tva="manuelle")
        cls.jour = datetime.date.today()
        cls.caisse = Journal.objects.get(code="CA")
        cls.client_ = Tiers.objects.create(code="CRAP", nom="Client rapport")
        cls.article = Article.objects.create(reference="HUILE", designation="Huile", prix_vente=1000, suivi_stock=False, taux_tva=0)
        cls.locale = Agence.objects.create(code="BTA", nom="Bertoua", locale=True)
        cls.garoua = Agence.objects.create(code="GBL", nom="Garoua-Boulaï")
        cls.charge = Compte.objects.filter(numero__startswith="6").order_by("numero").first()

    def piece(self, type_document, quantite, valider=True):
        doc = Document.objects.create(type_document=type_document, tiers=self.client_)
        LigneDocument.objects.create(document=doc, article=self.article, quantite=quantite, prix_unitaire=1000, taux_tva=0)
        doc.recalculer()
        if valider:
            doc.valider()
        return doc

    def regler(self, montant, **kwargs):
        return Reglement(tiers=self.client_, journal=self.caisse, montant=Decimal(montant), **kwargs).enregistrer()

    def test_versement_recu_par_une_autre_agence(self):
        facture = self.piece(Document.FACTURE, 4)                                    # 4 000 à crédit chez nous
        recu = Reglement(tiers=self.client_, journal=Journal.objects.get(code="OD"), montant=Decimal("4000"), facture=facture,
                         agence_encaissement=self.garoua, reference="GBL-R125")
        recu.enregistrer()
        facture.refresh_from_db()
        self.assertEqual(facture.reste_a_payer, 0)
        lignes = {l.compte.numero: l for l in recu.ecriture.lignes.all()}
        self.assertEqual(lignes[self.garoua.compte_liaison.numero].debit, Decimal("4000"))   # pas la caisse
        r = services.rapport_commercial(self.jour)
        self.assertEqual(r["recus_autres_agences"], [recu])
        self.assertEqual(r["encaissements"], [])                                     # aucun mouvement de notre caisse
        autre = self.piece(Document.FACTURE, 1)
        for erreur, kwargs in (("déjà enregistré", {"reference": "GBL-R125"}),         # même reçu saisi deux fois
                               ("n° du reçu", {"reference": ""}),
                               ("pas celle-ci", {"reference": "X1", "agence_encaissement": self.locale})):
            with self.assertRaisesMessage(ValidationError, erreur):
                Reglement(tiers=self.client_, journal=Journal.objects.get(code="OD"), montant=Decimal("1000"), facture=autre,
                          **{"agence_encaissement": self.garoua, **kwargs}).enregistrer()

    def test_client_au_comptant_signale(self):
        comptant = Tiers.objects.create(code="CCPT", nom="Client comptant", vente_credit=False)
        doc = Document.objects.create(type_document=Document.FACTURE, tiers=comptant)
        LigneDocument.objects.create(document=doc, article=self.article, quantite=1, prix_unitaire=1000, taux_tva=0)
        doc.recalculer()
        self.assertIn("client au comptant", doc.controler_encours())
        doc.valider()                                                                # signalé, jamais imposé
        natures = {l["doc"].pk: l["nature"] for l in services.rapport_commercial(self.jour)["ventes"]["factures"]}
        self.assertEqual(natures[doc.pk], "En compte · client au comptant non soldé")

    def test_recu_sans_facture_refuse(self):
        with self.assertRaisesMessage(ValidationError, "rattaché à la facture"):
            self.regler(1000)

    def test_auteurs_enregistres(self):
        chef = get_user_model().objects.create_superuser("caissiere", "", "x")
        self.client.force_login(chef)
        doc = self.piece(Document.FACTURE, 1, valider=False)
        self.client.post(reverse("commercial:document_valider", args=[doc.pk]))
        doc.refresh_from_db()
        self.assertEqual((doc.statut, doc.valide_par), (Document.VALIDE, chef))
        self.assertIsNotNone(doc.valide_le)
        page = self.client.get(reverse("commercial:document_detail", args=[doc.pk]))
        self.assertContains(page, "Validé le")
        self.assertContains(page, "par <strong>caissiere</strong>")

    def test_agence_et_compte_de_liaison(self):
        self.assertTrue(self.garoua.compte_liaison.numero.startswith("185"))
        self.assertIsNone(Agence.objects.get(code="BTA").compte_liaison)
        Agence.objects.create(code="ABM", nom="Abong-Mbang", locale=True)            # une seule agence locale
        self.assertEqual(list(Agence.objects.filter(locale=True).values_list("code", flat=True)), ["ABM"])

    def test_rapport_complet_du_jour(self):
        comptant = self.piece(Document.FACTURE, 2)                                   # 2 000 payés le jour
        self.regler(2000, facture=comptant)
        credit = self.piece(Document.FACTURE, 3)                                     # 3 000 à crédit
        commande = self.piece(Document.COMMANDE, 5)                                  # 5 000 payés d'avance
        self.regler(5000, commande=commande)
        hors = OperationCaisse(nature=OperationCaisse.HORS_RECETTE, journal=self.caisse, montant=Decimal("1500"),
                               libelle="Versement client", agence=self.garoua, tiers_libre="C0420 Client de Garoua").enregistrer()
        OperationCaisse(nature=OperationCaisse.DEPENSE, journal=self.caisse, montant=Decimal("700"), libelle="Carburant",
                        compte=self.charge).enregistrer()
        OperationCaisse(nature=OperationCaisse.SORTIE_AGENCE, journal=self.caisse, montant=Decimal("300"), libelle="Frais",
                        agence=self.garoua).enregistrer()
        r = services.rapport_commercial(self.jour)
        natures = {l["doc"].pk: l["nature"] for l in r["ventes"]["factures"]}
        self.assertEqual((natures[comptant.pk], natures[credit.pk]), ("Comptant", "En compte"))
        self.assertEqual((r["ventes"]["comptant"], r["ventes"]["credit"]), (Decimal("2000"), Decimal("3000")))
        self.assertEqual(r["ventes"]["commandes"][0]["nature"], "Payé d'avance")
        self.assertEqual(sorted(e["nature"] for e in r["encaissements"]), ["Acompte sur commande", "Vente du jour"])
        self.assertEqual(r["total_hors_recettes"], Decimal("1500"))
        self.assertEqual(r["solde"]["sorties"], Decimal("1000"))
        self.assertEqual(r["solde"]["cloture"], r["solde"]["ouverture"] + Decimal("8500") - Decimal("1000"))   # 2 000 + 5 000 + 1 500 entrés
        self.assertEqual(r["solde"]["ecart"], 0)                                      # rapproché du compte de caisse
        ligne_liaison = hors.ecriture.lignes.get(compte=self.garoua.compte_liaison)
        self.assertEqual(ligne_liaison.credit, Decimal("1500"))                       # hors recette : crédit liaison

    def test_acompte_impute_sur_la_facture_issue_de_la_commande(self):
        commande = self.piece(Document.COMMANDE, 4)
        acompte = self.regler(4000, commande=commande)
        self.assertEqual(acompte.montant_non_impute, Decimal("4000"))               # attend la facture
        livraison = commande.transformer(Document.LIVRAISON)
        livraison.valider()
        facture = livraison.transformer(Document.FACTURE)
        facture.valider()
        facture.refresh_from_db()
        self.assertEqual(facture.reste_a_payer, 0)
        r = services.rapport_commercial(self.jour)
        ligne = next(l for l in r["ventes"]["factures"] if l["doc"].pk == facture.pk)
        self.assertEqual(ligne["encaisse"], Decimal("4000"))                         # acompte versé le jour même

    def test_operation_d_agence_sans_agence_refusee(self):
        with self.assertRaises(ValidationError):
            OperationCaisse(nature=OperationCaisse.HORS_RECETTE, journal=self.caisse, montant=Decimal("10"), libelle="X").enregistrer()
        with self.assertRaises(ValidationError):
            OperationCaisse(nature=OperationCaisse.HORS_RECETTE, journal=self.caisse, montant=Decimal("10"), libelle="X",
                            agence=self.locale).enregistrer()

    def test_ecrans(self):
        self.client.force_login(get_user_model().objects.create_superuser("chef", "", "x"))
        url = reverse("commercial:rapport_commercial")
        self.assertTemplateUsed(self.client.get(url), "core/selection.html")
        self.assertContains(self.client.get(url + "?ok=1"), "Solde de clôture")
        reponse = self.client.post(reverse("commercial:operation_caisse_create"), {
            "date": self.jour.isoformat(), "nature": OperationCaisse.DEPENSE, "journal": self.caisse.pk, "montant": "250",
            "libelle": "Eau", "compte": self.charge.pk})
        self.assertEqual(reponse.status_code, 302)
        self.assertContains(self.client.get(reverse("commercial:operations_caisse")), "Eau")
        self.assertContains(self.client.get(reverse("commercial:agences")), "Garoua-Boulaï")
