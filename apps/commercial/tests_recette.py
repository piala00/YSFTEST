"""Cahier de recette « SAHEL DISTRIBUTION ».

Rejoue les cas pratiques du skill `sage-100-gescom-v12-formateur-expert`
(exercices/01-societe-fictive.md et 02-cas-pratiques-corriges.md) ainsi que les ateliers
2.2 (catégories tarifaires), 5.4 (réapprovisionnement) et 6.2 (encours) dans l'ERP.
Chaque test vérifie la « preuve » demandée par le corrigé : stock avant/après, reliquat,
solde du tiers, chaîne documentaire. Données entièrement fictives.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.comptabilite.models import Journal
from apps.core.models import Exercice

from . import reappro, sahel
from .models import (Article, CategorieTarifaire, Depot, Document, FamilleArticle, Inventaire, LigneDocument, MouvementStock,
                     Reglement, StockDepot, TarifCategorie, Tiers)

D = Decimal


class SahelDistribution(TestCase):
    """Société fictive décrite dans exercices/01-societe-fictive.md."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.exercice = Exercice.objects.first()
        cls.date = cls.exercice.date_debut
        cls.societe = sahel.creer_societe()
        d, f, a, c = cls.societe["depots"], cls.societe["familles"], cls.societe["articles"], cls.societe["categories"]
        cls.principal, cls.boutique, cls.boissons = d["DPT-PRINCIPAL"], d["DPT-BOUTIQUE"], d["DPT-BOISSONS"]
        cls.f_boissons = f["BOISSONS"]
        cls.jus, cls.eau, cls.riz, cls.transport = a["JUS-001"], a["EAU-001"], a["RIZ-025"], a["TRANS-001"]
        cls.transport.prix_vente = 150000
        cls.transport.save()
        cls.gros, cls.detail = c["GROS"], c["DETAIL"]
        cls.cli_gros, cls.cli_detail, cls.cli_enc = (cls.societe["clients"][k] for k in ("CLI-GROS-01", "CLI-DETAIL-01", "CLI-ENC-01"))
        cls.fou_bois = cls.societe["fournisseurs"]["FOU-BOIS-01"]
        # Pour l'atelier 5.4 : l'eau n'a pas de fournisseur principal
        cls.eau.fournisseur_principal = None
        cls.eau.save()

    def setUp(self):
        sahel.saisir_stocks_initiaux(self.societe, self.date)

    # --- outils -----------------------------------------------------------
    def stock(self, article, depot=None):
        article.refresh_from_db()
        return StockDepot.quantite_de(article.pk, depot.pk) if depot else article.stock

    def piece(self, type_document, tiers=None, lignes=(), **champs):
        doc = Document.objects.create(type_document=type_document, tiers=tiers, date=self.date, **champs)
        for article, quantite, *prix in lignes:
            prix_unitaire = prix[0] if prix else (article.prix_pour(tiers)[0] if tiers and tiers.est_client else article.prix_achat)
            LigneDocument.objects.create(document=doc, article=article, quantite=quantite, prix_unitaire=prix_unitaire)
        doc.recalculer()
        return doc

    def solde(self, tiers):
        return tiers.solde_comptable()


class CasPratiquesTests(SahelDistribution):
    def test_situation_initiale(self):
        self.assertEqual(self.stock(self.jus), D("200"))
        self.assertEqual(self.stock(self.eau, self.boissons), D("150"))
        self.assertEqual(self.stock(self.riz, self.boissons), D("0"))
        self.assertEqual(MouvementStock.objects.filter(document__reference_externe="STOCK-INITIAL").count(), 8)

    def test_cas_03_article_jus_dans_boissons(self):
        article = Article.objects.get(reference="JUS-001")
        self.assertEqual(article.famille.code, "BOISSONS")
        self.assertTrue(article.suivi_stock)
        self.assertEqual(article.get_compte_vente().numero, "701")      # marchandise
        self.assertEqual(article.cmup, D("800"))                        # valorisé par les entrées

    def test_cas_04_tarification_gros_et_detail(self):
        devis_gros = self.piece(Document.DEVIS, self.cli_gros, [(self.jus, 10)])
        devis_detail = self.piece(Document.DEVIS, self.cli_detail, [(self.jus, 10)])
        self.assertEqual(devis_gros.lignes.get().prix_unitaire, D("1200"))
        self.assertEqual(devis_detail.lignes.get().prix_unitaire, D("1500"))
        # La source du prix est traçable
        self.assertEqual(self.jus.prix_pour(self.cli_gros), (D("1200"), "catégorie tarifaire Gros"))
        self.assertEqual(self.jus.prix_pour(self.cli_detail), (D("1500"), "catégorie tarifaire Détail"))
        self.assertEqual(self.jus.prix_pour(self.cli_enc), (D("1500"), "fiche article"))   # sans catégorie

    def test_cas_05_entree_au_depot_principal(self):
        avant = self.stock(self.jus, self.principal)
        entree = self.piece(Document.STOCK_ENTREE, lignes=[(self.jus, 100, 800)], depot=self.principal).valider()
        self.assertEqual(self.stock(self.jus, self.principal), avant + 100)
        self.assertEqual(entree.mouvements_stock.get().quantite, D("100"))
        self.assertIsNone(entree.ecriture)   # mouvement interne : pas d'écriture comptable

    def test_cas_06_transfert_principal_vers_boutique(self):
        a, b, total = self.stock(self.jus, self.principal), self.stock(self.jus, self.boutique), self.stock(self.jus)
        self.piece(Document.STOCK_VIREMENT, lignes=[(self.jus, 25, 0)], depot=self.principal,
                   depot_destination=self.boutique).valider()
        self.assertEqual(self.stock(self.jus, self.principal), a - 25)
        self.assertEqual(self.stock(self.jus, self.boutique), b + 25)
        self.assertEqual(self.stock(self.jus), total)               # total tous dépôts inchangé
        self.assertFalse(Document.objects.filter(type_document=Document.FACTURE).exists())   # pas une vente

    def test_cas_07_chaine_devis_commande_livraison_facture(self):
        releve = []
        devis = self.piece(Document.DEVIS, self.cli_gros, [(self.jus, 10)]).valider()
        releve.append(("devis", self.stock(self.jus, self.principal)))
        commande = devis.transformer(Document.COMMANDE); commande.valider()
        releve.append(("commande", self.stock(self.jus, self.principal)))
        bl = commande.transformer(Document.LIVRAISON); bl.valider()
        releve.append(("livraison", self.stock(self.jus, self.principal)))
        facture = bl.transformer(Document.FACTURE); facture.valider()
        releve.append(("facture", self.stock(self.jus, self.principal)))
        # Seul le bon de livraison mouvemente le stock
        self.assertEqual([q for _, q in releve], [D("100"), D("100"), D("90"), D("90")])
        self.assertEqual(MouvementStock.objects.filter(document__in=[devis, commande, bl, facture]).count(), 1)
        # Chaîne traçable et créance constatée par la facture seulement
        self.assertEqual((facture.origine, bl.origine, commande.origine), (bl, commande, devis))
        self.assertEqual(self.solde(self.cli_gros), facture.total_ttc)

    def test_cas_08_livraison_partielle_6_sur_10(self):
        commande = self.piece(Document.COMMANDE, self.cli_gros, [(self.jus, 10)]).valider()
        bl = commande.transformer(Document.LIVRAISON)
        ligne = bl.lignes.get(); ligne.quantite = 6; ligne.save(); bl.recalculer()
        bl.valider()
        commande.refresh_from_db()
        self.assertTrue(commande.partiellement_transforme)
        self.assertEqual(commande.lignes.get().reste_a_transformer, D("4"))
        self.assertEqual(self.stock(self.jus, self.principal), D("94"))

    def test_cas_09_achat_reception_partielle_20_sur_30(self):
        avant = self.stock(self.jus, self.principal)
        commande = self.piece(Document.ACHAT_COMMANDE, self.fou_bois, [(self.jus, 30, 800)], depot=self.principal).valider()
        self.assertEqual(self.stock(self.jus, self.principal), avant)          # la commande n'est qu'un engagement
        reception = commande.transformer(Document.ACHAT_RECEPTION)
        ligne = reception.lignes.get(); ligne.quantite = 20; ligne.save(); reception.recalculer()
        reception.valider()
        commande.refresh_from_db()
        self.assertEqual(commande.lignes.get().reste_a_transformer, D("10"))   # reste à recevoir
        self.assertEqual(self.stock(self.jus, self.principal), avant + 20)
        facture = reception.transformer(Document.ACHAT_FACTURE)
        self.assertEqual(facture.lignes.get().quantite, D("20"))              # on facture ce qui est reçu
        facture.valider()
        self.assertEqual(self.stock(self.jus, self.principal), avant + 20)     # pas de double entrée
        self.assertEqual(self.solde(self.fou_bois), -facture.total_ttc)

    def test_cas_10_inventaire_75_compte_73(self):
        # Ramène le stock théorique du dépôt boutique à 75 puis compte 73
        self.piece(Document.STOCK_ENTREE, lignes=[(self.jus, 55, 800)], depot=self.boutique).valider()
        self.assertEqual(self.stock(self.jus, self.boutique), D("75"))
        inventaire = Inventaire.objects.create(depot=self.boutique, famille=self.f_boissons, notes="Comptage annuel")
        inventaire.initialiser_lignes()
        ligne = inventaire.lignes.get(article=self.jus)
        self.assertEqual(ligne.stock_theorique, D("75"))
        ligne.stock_reel = D("73"); ligne.save()
        self.assertEqual(ligne.ecart, D("-2"))
        inventaire.valider()
        self.assertEqual(self.stock(self.jus, self.boutique), D("73"))
        sortie = inventaire.mouvement_sortie
        self.assertEqual((sortie.type_document, sortie.reference_externe), (Document.STOCK_SORTIE, inventaire.numero))
        self.assertEqual(sortie.mouvements_stock.get().quantite, D("-2"))

    def test_cas_11_reglement_partiel_150000_puis_solde(self):
        self.cli_detail.assujetti_tva = False      # TTC = HT pour l'exercice
        self.cli_detail.save()
        facture = self.piece(Document.FACTURE, self.cli_detail, [(self.transport, 1, 150000)]).valider()
        self.assertEqual(facture.total_ttc, D("150000"))
        caisse = Journal.objects.get(code="CA")
        Reglement(tiers=self.cli_detail, journal=caisse, montant=D("50000"), date=self.date).enregistrer()
        facture.refresh_from_db()
        self.assertEqual(facture.reste_a_payer, D("100000"))
        self.assertEqual(self.solde(self.cli_detail), D("100000"))
        self.assertEqual(self.stock(self.jus), D("200"))     # un encaissement ne touche pas le stock
        Reglement(tiers=self.cli_detail, journal=caisse, montant=D("100000"), date=self.date).enregistrer()
        facture.refresh_from_db()
        self.assertEqual(facture.reste_a_payer, D("0"))
        self.assertEqual(self.solde(self.cli_detail), D("0"))

    def test_cas_12_depassement_du_plafond_d_encours(self):
        # CLI-ENC-01 : plafond 100 000, code risque « blocage ». Comme dans Sage (aide « encours client »), devis et
        # commandes restent possibles avec un message ; la livraison et la facture sont refusées.
        livraison = self.piece(Document.LIVRAISON, self.cli_enc, [(self.riz, 10)])    # 160 000 HT
        with self.assertRaises(ValidationError):
            livraison.valider()
        livraison.refresh_from_db()
        self.assertEqual(livraison.statut, Document.BROUILLON)
        commande_message = self.piece(Document.COMMANDE, self.cli_enc, [(self.riz, 10)]).valider()
        self.assertIn("dépassement", commande_message.avertissement)
        commande = self.piece(Document.FACTURE, self.cli_enc, [(self.riz, 10)])
        # En dessous du plafond, la pièce passe
        petite = self.piece(Document.COMMANDE, self.cli_enc, [(self.eau, 10)]).valider()
        self.assertIsNone(petite.avertissement)
        # Code risque « avertissement » : la pièce est validée mais signalée
        self.cli_enc.code_risque = Tiers.RISQUE_AVERTIR
        self.cli_enc.save()
        commande.tiers.refresh_from_db()
        commande.valider()
        self.assertEqual(commande.statut, Document.VALIDE)
        self.assertIn("dépassement", commande.avertissement)
        # Les devis ne sont pas contrôlés
        self.cli_enc.code_risque = Tiers.RISQUE_BLOQUER
        self.cli_enc.save()
        self.piece(Document.DEVIS, self.cli_enc, [(self.riz, 50)]).valider()

    def test_cas_13_retour_physique_et_avoir_distincts(self):
        facture = self.piece(Document.FACTURE, self.cli_gros, [(self.jus, 10)]).valider()
        stock_apres_vente, du = self.stock(self.jus, self.principal), self.solde(self.cli_gros)
        # Retour physique de 2 unités : bon de retour → stock, sans effet financier
        bl = self.piece(Document.LIVRAISON, self.cli_gros, [(self.jus, 2)]).valider()
        retour = bl.transformer(Document.RETOUR); retour.valider()
        self.assertEqual(self.stock(self.jus, self.principal), stock_apres_vente)   # -2 (BL) puis +2 (retour)
        facture_retour = retour.transformer(Document.FACTURE_RETOUR); facture_retour.valider()
        self.assertEqual(self.stock(self.jus, self.principal), stock_apres_vente)   # pas de double entrée
        self.assertEqual(self.solde(self.cli_gros), du - facture_retour.total_ttc)
        # Avoir financier (geste commercial) : créance réduite, stock inchangé
        avoir = facture.transformer(Document.AVOIR)
        ligne = avoir.lignes.get(); ligne.quantite = 1; ligne.save(); avoir.recalculer()
        avoir.valider()
        self.assertEqual(self.stock(self.jus, self.principal), stock_apres_vente)
        self.assertEqual(self.solde(self.cli_gros), du - facture_retour.total_ttc - avoir.total_ttc)
        # Un avoir n'est pas un règlement : la facture d'origine reste due
        facture.refresh_from_db()
        self.assertEqual(facture.reste_a_payer, facture.total_ttc)

    def test_cas_14_etat_de_vente_concilie_avec_trois_pieces(self):
        from apps.reporting import services, statistiques

        f1 = self.piece(Document.FACTURE, self.cli_gros, [(self.jus, 10)]).valider()       # 12 000 HT
        f2 = self.piece(Document.FACTURE, self.cli_detail, [(self.eau, 20)]).valider()     # 9 000 HT
        avoir = f1.transformer(Document.AVOIR)
        ligne = avoir.lignes.get(); ligne.quantite = 2; ligne.save(); avoir.recalculer()
        avoir.valider()                                                                     # -2 400 HT
        self.piece(Document.DEVIS, self.cli_gros, [(self.riz, 5)]).valider()               # exclu : un devis
        brouillon = self.piece(Document.FACTURE, self.cli_gros, [(self.riz, 1)])            # exclu : non validée
        attendu = f1.total_ht + f2.total_ht - avoir.total_ht
        self.assertEqual(attendu, D("18600"))
        fin = self.exercice.date_fin
        self.assertEqual(services.chiffre_affaires(self.date, fin), attendu)
        etat = statistiques.calculer("palmares_clients", self.date, fin)
        self.assertEqual(etat["totaux"]["montant"], attendu)
        self.assertEqual({l["code"]: l["montant"] for l in etat["lignes"]},
                         {"CLI-GROS-01": f1.total_ht - avoir.total_ht, "CLI-DETAIL-01": f2.total_ht})
        self.assertEqual(brouillon.statut, Document.BROUILLON)


class AteliersTests(SahelDistribution):
    def test_atelier_5_4_reapprovisionnement_mini_maxi_par_depot(self):
        # Seuils distincts sur deux dépôts ; seul la boutique passe sous son mini
        StockDepot.objects.filter(article=self.jus, depot=self.boutique).update(stock_mini=30, stock_maxi=60)
        StockDepot.objects.filter(article=self.jus, depot=self.principal).update(stock_mini=50, stock_maxi=150)
        propositions = reappro.propositions()
        self.assertEqual([(s.article.reference, s.depot.code, s.besoin) for s in propositions],
                         [("JUS-001", "DPT-BOUTIQUE", D("40"))])                 # 60 - 20
        commandes, sans_fournisseur = reappro.generer_commandes([(propositions[0], propositions[0].besoin)])
        self.assertEqual(sans_fournisseur, [])
        commande = commandes[0]
        self.assertEqual((commande.type_document, commande.statut, commande.tiers, commande.depot),
                         (Document.ACHAT_COMMANDE, Document.BROUILLON, self.fou_bois, self.boutique))
        self.assertEqual(commande.lignes.get().quantite, D("40"))
        # Sans fournisseur principal, la ligne est signalée et ignorée
        StockDepot.objects.filter(article=self.eau, depot=self.boutique).update(stock_mini=50, stock_maxi=80)
        ligne_eau = next(s for s in reappro.propositions() if s.article == self.eau)
        commandes, sans_fournisseur = reappro.generer_commandes([(ligne_eau, ligne_eau.besoin)])
        self.assertEqual((commandes, sans_fournisseur), ([], [ligne_eau]))

    def test_ecrans_de_la_recette(self):
        utilisateur = get_user_model().objects.create_superuser("formateur", "", "pwd")
        self.client.force_login(utilisateur)
        StockDepot.objects.filter(article=self.jus, depot=self.boutique).update(stock_mini=30, stock_maxi=60)
        # Gestion des besoins → génération d'un bon de commande en brouillon
        page = self.client.get(reverse("commercial:besoins"))
        self.assertContains(page, "JUS-001")
        stock = StockDepot.objects.get(article=self.jus, depot=self.boutique)
        reponse = self.client.post(reverse("commercial:besoins"), {f"choisir_{stock.pk}": "on", f"quantite_{stock.pk}": "40"})
        commande = Document.objects.get(type_document=Document.ACHAT_COMMANDE)
        self.assertRedirects(reponse, reverse("commercial:document_detail", args=[commande.pk]))
        # Fiche article : tarifs et seuils enregistrés depuis l'écran
        self.client.post(reverse("commercial:article_parametres", args=[self.riz.pk]),
                         {f"tarif_{self.gros.pk}": "15\u202f000", f"tarif_{self.detail.pk}": "",
                          f"mini_{self.principal.pk}": "10", f"maxi_{self.principal.pk}": "40"})
        self.assertEqual(TarifCategorie.objects.get(article=self.riz, categorie=self.gros).prix_vente, D("15000"))
        self.assertFalse(TarifCategorie.objects.filter(article=self.riz, categorie=self.detail).exists())
        self.assertEqual(StockDepot.objects.get(article=self.riz, depot=self.principal).stock_maxi, D("40"))
        # La fiche réaffiche des valeurs que l'on peut renvoyer telles quelles
        fiche = self.client.get(reverse("commercial:article_detail", args=[self.riz.pk])).content.decode()
        self.assertIn(f'name="tarif_{self.gros.pk}" value="15000.00"', fiche)
        # Encours : la validation bloquée est expliquée à l'utilisateur
        commande_bloquee = self.piece(Document.FACTURE, self.cli_enc, [(self.riz, 10)])
        reponse = self.client.post(reverse("commercial:document_valider", args=[commande_bloquee.pk]), follow=True)
        self.assertContains(reponse, "Validation refusée")
        for url in (reverse("commercial:categories"), reverse("commercial:categorie_create"),
                    reverse("commercial:article_detail", args=[self.jus.pk]), reverse("commercial:tiers_detail", args=[self.cli_enc.pk]),
                    reverse("commercial:document_create", args=["DEVIS"])):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class EcransEtatsV12Tests(TestCase):
    """Skill GPT sage100-ecrans-etats-v12 : compte bloqué et transformation d'achat documentée V12.20."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.client_ = Tiers.objects.create(code="CBLOQ", nom="Client bloqué", compte_bloque=True)
        cls.fournisseur = Tiers.objects.create(code="FPREP", nom="Fournisseur", type_tiers=Tiers.FOURNISSEUR)
        cls.article = Article.objects.create(reference="ABLOQ", designation="Article", prix_vente=1000, prix_achat=500)

    def test_compte_bloque_aucun_document(self):
        for type_document in (Document.DEVIS, Document.COMMANDE):
            doc = Document(type_document=type_document, tiers=self.client_)
            with self.assertRaises(ValidationError):
                doc.clean()

    def test_preparation_de_commande_vers_bon_de_livraison(self):
        prep = Document.objects.create(type_document=Document.ACHAT_PREPARATION, tiers=self.fournisseur)
        LigneDocument.objects.create(document=prep, article=self.article, quantite=5, prix_unitaire=500)
        prep.recalculer()
        prep.valider()
        reception = prep.transformer(Document.ACHAT_RECEPTION, None)
        self.assertEqual(reception.type_document, Document.ACHAT_RECEPTION)
