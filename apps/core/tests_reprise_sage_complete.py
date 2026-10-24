"""Reprise complète d'un dossier Sage 100 : comptabilité (journaux, analytique, taxes, écritures lettrées) et gestion
commerciale (tarifs, pièces en cours et historique, échéances, règlements en attente).

Jeu fictif `reprise_sage/exemple_complet` : CSV produits par la lecture directe (SourceSQL) de la base fictive
`exemple_sql/base_sage_fictive.sql` montée sur SQL Server 2022 — les deux chemins lisent les mêmes données.
"""
import datetime
from decimal import Decimal
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from apps.commercial.models import Article, Depot, Document, Reglement, StockDepot, TarifCategorie, Tiers
from apps.comptabilite import services
from apps.comptabilite.models import Ecriture, Journal, LigneEcriture, SectionAnalytique, Taxe
from apps.core import reprise_sage
from apps.core.reprise_sage.source import Requetes, SourceSQL

EXEMPLE = Path(reprise_sage.__file__).with_name("exemple_complet")
BASCULE, DEBUT = datetime.date(2026, 10, 31), datetime.date(2026, 1, 1)


class RepriseCompleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)

    def importer(self, appliquer=True):
        return reprise_sage.importer(EXEMPLE, BASCULE, appliquer=appliquer, debut_exercice=DEBUT)

    def test_simulation_conforme_sans_rien_enregistrer(self):
        rapport = self.importer(appliquer=False)
        self.assertTrue(rapport.conforme, rapport.texte())
        self.assertFalse(Document.objects.exclude(reprise_sage="").exists())
        self.assertFalse(Ecriture.objects.filter(reference__startswith="SAGE ").exists())
        noms = [c[0] for c in rapport.controles]
        self.assertIn("Écritures : total débit origine = ERP", noms)
        self.assertIn("Créances et dettes : pièces reprises = soldes comptables des tiers", noms)

    def test_comptabilite_reprise(self):
        rapport = self.importer()
        self.assertTrue(rapport.conforme, rapport.texte())
        # Journaux (situation exclu), comptes (total exclu), taxes, sections (même code dans deux plans)
        self.assertEqual(Journal.objects.get(code="BQ1").compte_tresorerie.numero, "521100")
        self.assertEqual(Journal.objects.get(code="VTE").type_journal, Journal.TYPE_VENTE)
        self.assertFalse(Journal.objects.filter(code="SIT").exists())
        self.assertEqual(Taxe.objects.get(code="T19").sens, Taxe.COLLECTEE)
        self.assertEqual(SectionAnalytique.objects.get(code="2-AG01").plan, "Plan analytique 2")
        # Écritures : exercice jusqu'à la bascule, sans situation, IFRS seule ni postérieures
        lignes = LigneEcriture.objects.filter(ecriture__reference__startswith="SAGE ")
        self.assertEqual(sum(l.debit for l in lignes), sum(l.credit for l in lignes))
        self.assertFalse(lignes.filter(ecriture__journal__code="SIT").exists())
        self.assertEqual(Tiers.objects.get(code="CL001").solde_comptable(), Decimal("69250"))
        # Lettrage conservé ; ventilation analytique du premier plan, montant non doublé
        self.assertEqual(lignes.filter(lettrage="A").count(), 2)
        ventes_fa001 = lignes.filter(ecriture__reference="SAGE FA001", compte__numero="701100")
        self.assertEqual(sorted((l.section.code, l.credit) for l in ventes_fa001),
                         [("AG01", Decimal("150000")), ("AG02", Decimal("50000"))])
        self.assertIn("second plan analytique", " ".join(rapport.avertissements))
        # Salarié : ligne sur son compte, sans fiche tiers
        self.assertIsNone(lignes.get(compte__numero="421000").tiers)

    def test_gestion_commerciale_reprise(self):
        self.assertTrue(self.importer().conforme)
        piece = lambda n: Document.objects.get(numero=n)
        self.assertEqual((piece("FA001").reste_a_payer, piece("FA002").reste_a_payer, piece("FA003").reste_a_payer),
                         (0, Decimal("69250"), Decimal("59625")))
        self.assertEqual(piece("FF001").type_document, Document.ACHAT_FACTURE)
        self.assertEqual(piece("AV001").type_document, Document.AVOIR)            # DO_Provenance 2
        self.assertEqual(piece("FA002").date_echeance, datetime.date(2026, 11, 4))
        self.assertFalse(Document.objects.filter(numero__in=["FA000", "AR0001"]).exists())   # soldée ancienne, archive
        self.assertTrue(Document.objects.filter(numero="DE0001").exists())       # pièce en cours, quelle que soit sa date
        for doc in Document.objects.exclude(reprise_sage=""):
            self.assertFalse(doc.mouvements_stock.exists())                       # le stock vient de F_ARTSTOCK
            self.assertIsNone(doc.ecriture_id)                                    # la compta vient des écritures Sage
        en_attente = Reglement.objects.get(numero="RS-3")
        self.assertEqual((en_attente.tiers.code, en_attente.en_attente_de_rattachement), ("CL002", Decimal("30000")))
        self.assertEqual(TarifCategorie.objects.get().prix_vente, Decimal("11000"))
        self.assertEqual(Tiers.objects.get(code="CL001").categorie_tarifaire.code, "CAT1")
        self.assertEqual(StockDepot.quantite_de(Article.objects.get(reference="HUI15").pk, Depot.objects.get(code="1").pk), 40)
        self.assertEqual(services.controle_liaison(DEBUT, BASCULE)["anomalies"], [])

    def test_continuer_dans_l_erp(self):
        self.assertTrue(self.importer().conforme)
        caisse = Journal.objects.get(code="CA")
        facture = Document.objects.get(numero="BL0001").transformer(Document.FACTURE).valider()   # BL repris facturé
        self.assertIsNotNone(facture.ecriture)
        livraison = Document.objects.get(numero="BC0001").transformer(Document.LIVRAISON)        # commande reprise livrée
        livraison.valider()
        self.assertEqual(StockDepot.quantite_de(Article.objects.get(reference="HUI15").pk, Depot.objects.get(code="1").pk), 37)
        fa2 = Document.objects.get(numero="FA002")
        Reglement(tiers=fa2.tiers, journal=caisse, montant=Decimal("69250")).enregistrer([fa2])
        Reglement.objects.get(numero="RS-3").rattacher(Document.objects.get(numero="FA003"))
        fa2.refresh_from_db()
        self.assertEqual((fa2.reste_a_payer, Document.objects.get(numero="FA003").reste_a_payer), (0, Decimal("29625")))

    def test_reprise_rejouable_sans_doublon(self):
        self.assertTrue(self.importer().conforme)
        ecritures, pieces = Ecriture.objects.count(), Document.objects.count()
        rapport = self.importer()
        self.assertTrue(rapport.conforme, rapport.texte())
        self.assertEqual((Ecriture.objects.count(), Document.objects.count()), (ecritures, pieces))
        self.assertIn("déjà reprises", rapport.texte())


class RequetesSageTests(TestCase):
    def test_colonnes_absentes_omises(self):
        presentes = {"F_ECRITUREC": {"EC_No", "JO_Num", "JM_Date", "EC_Jour", "EC_Piece", "CG_Num", "CT_Num", "EC_Sens",
                                     "EC_Montant"}, "F_JOURNAUX": {"JO_Num"}}
        sql = Requetes(DEBUT, BASCULE, presentes=presentes).sql("ecritures")
        self.assertNotIn("EC_Lettrage", sql)                     # facultative absente : omise
        self.assertNotIn("EC_Norme", sql)
        self.assertIn("EC_DateCompta", sql)
        self.assertTrue(sql.startswith("SELECT"))

    def test_seuls_les_select_sont_executes(self):
        class Connexion:
            def cursor(self):
                raise AssertionError("aucune requête ne doit partir")

        source = SourceSQL.__new__(SourceSQL)
        source.connexion = Connexion()
        for sql in ("DELETE FROM F_COMPTET", "SELECT 1; DROP TABLE F_COMPTET", "UPDATE F_ARTICLE SET AR_PrixVen = 0"):
            with self.assertRaises(PermissionError):
                source._executer(sql)

    def test_script_export_en_lecture_seule(self):
        import re

        from apps.core.reprise_sage.source import script_export

        texte = re.sub(r"/\*.*?\*/|--[^\n]*", "", script_export(DEBUT, BASCULE), flags=re.S)
        self.assertNotRegex(texte, r"(?i)\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC(?:UTE)?|DBCC|INTO)\b")


class EcranRepriseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)

    def test_ecran_reserve_a_l_administrateur(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        url = reverse("commercial:reprise_dossier") + "?seul=1"
        self.client.force_login(get_user_model().objects.create_user("vendeur", "", "x"))
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(get_user_model().objects.create_superuser("admin", "", "x"))
        page = self.client.get(url)
        self.assertContains(page, "Simuler")
        self.assertNotContains(page, "Sage")                                   # aucun nom de l'ancien logiciel affiché
        reponse = self.client.post(url, {"action": "simuler", "serveur": "serveur-inexistant.invalid", "base": "X",
                                         "debut_exercice": "2026-01-01", "date_bascule": "2026-10-31"}, follow=True)
        self.assertContains(reponse, "Reprise impossible")
        self.assertFalse(Document.objects.exclude(reprise_sage="").exists())
