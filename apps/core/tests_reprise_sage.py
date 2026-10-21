"""Reprise d'un dossier Sage 100 depuis les CSV des SELECT de lecture seule (jeu d'exemple fictif)."""
import re
import shutil
import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.commercial.models import Article, Depot, Document, FamilleArticle, StockDepot, Tiers
from apps.comptabilite.models import Ecriture
from apps.comptabilite.services import balance
from apps.core import reprise_sage
from apps.core.models import Exercice

EXEMPLE = Path(reprise_sage.__file__).with_name("exemple")


class RepriseSageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.date = Exercice.objects.first().date_debut

    def setUp(self):
        self.dossier = Path(tempfile.mkdtemp())
        for f in EXEMPLE.glob("*.csv"):
            shutil.copy(f, self.dossier)
        self.addCleanup(shutil.rmtree, self.dossier)

    def importer(self, appliquer=True):
        return reprise_sage.importer(self.dossier, self.date, appliquer=appliquer)

    def test_simulation_n_enregistre_rien(self):
        rapport = self.importer(appliquer=False)
        self.assertTrue(rapport.conforme, rapport.texte())
        self.assertTrue(rapport.simulation)
        self.assertEqual(rapport.bilans["tiers"].creees, 3)
        self.assertFalse(Tiers.objects.exists())
        self.assertFalse(Ecriture.objects.filter(reference=reprise_sage.REFERENCE_REPRISE).exists())

    def test_import_referentiels(self):
        rapport = self.importer()
        self.assertTrue(rapport.conforme, rapport.texte())
        self.assertEqual(Depot.objects.get(code="2").intitule, "Agence Garoua-Boulaï")
        self.assertTrue(FamilleArticle.objects.filter(code="CIMENT").exists())
        self.assertFalse(FamilleArticle.objects.filter(code="TOTAL").exists())      # FA_Type 1 ignoré
        client = Tiers.objects.get(code="CDUPONT")
        self.assertEqual(client.type_tiers, Tiers.CLIENT)
        self.assertEqual(client.compte_collectif.numero, "4111")
        self.assertEqual(Tiers.objects.get(code="FCIMENCAM").type_tiers, Tiers.FOURNISSEUR)
        self.assertFalse(Tiers.objects.filter(code="SALARIE1").exists())            # CT_Type 2 ignoré
        self.assertFalse(Tiers.objects.get(code="CANCIEN").actif)                   # en sommeil
        ciment = Article.objects.get(reference="CIM50")
        self.assertEqual((ciment.prix_achat, ciment.prix_vente), (Decimal("800"), Decimal("1000")))
        self.assertTrue(ciment.suivi_stock)
        self.assertFalse(Article.objects.get(reference="LIVR").suivi_stock)
        self.assertTrue(Depot.objects.get(code="1").principal)                       # remplace le dépôt créé à l'installation
        self.assertEqual(Depot.objects.filter(principal=True).count(), 1)
        self.assertEqual(rapport.bilans["depots"].anomalies, [])

    def test_plusieurs_depots_principaux_dans_sage(self):
        (self.dossier / "depots.csv").write_text("DE_No;DE_Intitule;DE_Principal\n1;A;1\n2;B;1\n", encoding="utf-8")
        rapport = self.importer(appliquer=False)
        self.assertIn("plusieurs dépôts principaux", " ".join(rapport.bilans["depots"].anomalies))

    def test_stock_d_ouverture_par_depot_et_cmup(self):
        self.importer()
        ciment = Article.objects.get(reference="CIM50")
        self.assertEqual(StockDepot.quantite_de(ciment.pk, Depot.objects.get(code="1").pk), Decimal("100"))
        self.assertEqual(StockDepot.quantite_de(ciment.pk, Depot.objects.get(code="2").pk), Decimal("10"))
        self.assertEqual(ciment.stock, Decimal("110"))
        self.assertEqual(ciment.valeur_stock, Decimal("88125"))
        stock = StockDepot.objects.get(article=ciment, depot__code="1")
        self.assertEqual((stock.stock_mini, stock.stock_maxi), (Decimal("20"), Decimal("200")))
        # Le stock est repris sans écriture : sa valeur comptable vient du compte 311 de soldes.csv
        reprise = Document.objects.filter(reference_externe=reprise_sage.REFERENCE_REPRISE)
        self.assertEqual(reprise.count(), 2)
        self.assertFalse(reprise.exclude(ecriture=None).exists())

    def test_soldes_d_ouverture(self):
        self.importer()
        ecriture = Ecriture.objects.get(reference=reprise_sage.REFERENCE_REPRISE)
        self.assertEqual(ecriture.journal.code, "AN")
        self.assertTrue(ecriture.equilibree)
        self.assertEqual(ecriture.total_debit, Decimal("1120000"))
        self.assertEqual(Tiers.objects.get(code="CDUPONT").solde_comptable(), Decimal("300000"))   # net 350 000 - 50 000
        lignes, totaux = balance(self.date, self.date)
        self.assertEqual(totaux["an_d"], totaux["an_c"])
        self.assertEqual({l["compte"].numero: l["an_d"] for l in lignes}["5211"], Decimal("600000"))

    def test_import_rejouable_sans_doublon(self):
        self.importer()
        rapport = self.importer()
        self.assertTrue(rapport.conforme, rapport.texte())
        self.assertEqual(rapport.bilans["tiers"].creees, 0)
        self.assertEqual(Ecriture.objects.filter(reference=reprise_sage.REFERENCE_REPRISE).count(), 1)
        self.assertEqual(Article.objects.get(reference="CIM50").stock, Decimal("110"))

    def test_soldes_desequilibres_bloquent_tout_l_import(self):
        chemin = self.dossier / "soldes.csv"
        chemin.write_text(chemin.read_text(encoding="utf-8").replace("131875", "131000"), encoding="utf-8")
        rapport = self.importer()
        self.assertFalse(rapport.conforme)
        self.assertTrue(rapport.simulation)
        self.assertFalse(Tiers.objects.exists())

    def test_colonne_obligatoire_absente(self):
        (self.dossier / "tiers.csv").write_text("CT_Num;CT_Intitule\nC1;Client\n", encoding="utf-8")
        rapport = self.importer()
        self.assertFalse(rapport.conforme)
        self.assertIn("CT_Type", " ".join(rapport.erreurs))

    def test_stock_negatif_signale(self):
        (self.dossier / "stocks.csv").write_text("AR_Ref;DE_No;AS_QteSto;AS_MontSto\nCIM50;1;-5;0\n", encoding="utf-8")
        rapport = self.importer(appliquer=False)
        self.assertIn("stock négatif", " ".join(rapport.bilans["stocks"].anomalies))

    def test_export_sql_en_lecture_seule(self):
        """Même contrôle que le validateur du skill : aucune instruction d'écriture hors commentaires."""
        texte = re.sub(r"/\*.*?\*/|--[^\n]*", "", reprise_sage.SQL_EXPORT.read_text(encoding="utf-8"), flags=re.S)
        self.assertNotRegex(texte, r"(?i)\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC(?:UTE)?|DBCC|INTO)\b")
        for nom, (table, colonnes) in reprise_sage.FICHIERS.items():
            self.assertIn(f"-- {nom}.csv", reprise_sage.SQL_EXPORT.read_text(encoding="utf-8"))
            self.assertIn(table, texte)

    def test_commande(self):
        sortie = StringIO()
        call_command("reprise_sage", correspondance=True, stdout=sortie)
        self.assertIn("À CONFIRMER", sortie.getvalue())
        call_command("reprise_sage", dossier=str(self.dossier), date_bascule=self.date.isoformat(), stdout=StringIO())
        self.assertFalse(Tiers.objects.exists())
        with self.assertRaises(CommandError):
            call_command("reprise_sage", dossier=str(self.dossier), date_bascule="31/12/2026", stdout=StringIO())
