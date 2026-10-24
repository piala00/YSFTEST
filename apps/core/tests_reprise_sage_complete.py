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
        return reprise_sage.importer(EXEMPLE, BASCULE, appliquer=appliquer, debut_exercice=DEBUT, dossier=str(EXEMPLE))

    def test_simulation_conforme_sans_rien_enregistrer(self):
        rapport = self.importer(appliquer=False)
        self.assertTrue(rapport.conforme, rapport.texte())
        self.assertFalse(Document.objects.exclude(reprise_sage="").exists())
        self.assertFalse(Ecriture.objects.filter(source_cle__startswith="ORIG|").exists())
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
        lignes = LigneEcriture.objects.filter(ecriture__source_cle__startswith="ORIG|")
        self.assertEqual(sum(l.debit for l in lignes), sum(l.credit for l in lignes))
        self.assertFalse(lignes.filter(ecriture__journal__code="SIT").exists())
        self.assertEqual(Tiers.objects.get(code="CL001").solde_comptable(), Decimal("69250"))
        # Lettrage conservé ; ventilation analytique du premier plan, montant non doublé
        self.assertEqual(lignes.filter(lettrage="A").count(), 2)
        ventes_fa001 = lignes.filter(ecriture__reference="FA001", compte__numero="701100")
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
        reprise_sage.basculer()                                                  # fin de la transition
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
        for nom in ("ecritures", "documents"):                                  # rien de changé : rien de refait
            b = rapport.bilans[nom]
            self.assertEqual((b.creees, b.mises_a_jour, b.supprimees), (0, 0, 0), nom)

    def test_copie_synchronisee_puis_bascule(self):
        from django.core.exceptions import ValidationError

        from apps.core.models import LotSynchronisation, Societe

        simulation = self.importer(appliquer=False)
        self.assertEqual(Societe.get().source_mode, "")                         # une simulation ne change rien
        self.assertTrue(self.importer().conforme)
        self.assertEqual(Societe.get().source_mode, Societe.SYNCHRO_MIROIR)
        self.assertEqual(LotSynchronisation.objects.count(), 2)
        self.assertFalse(LotSynchronisation.objects.last().applique)
        self.assertTrue(LotSynchronisation.objects.first().applique)
        fa2 = Document.objects.get(numero="FA002")
        with self.assertRaisesMessage(ValidationError, "Synchronisation en cours"):        # pas de double saisie
            Reglement(tiers=fa2.tiers, journal=Journal.objects.get(code="CA"), montant=Decimal("1000")).enregistrer([fa2])
        with self.assertRaisesMessage(ValidationError, "Synchronisation en cours"):
            Document.objects.get(numero="BC0001").transformer(Document.LIVRAISON)
        autre = reprise_sage.importer(EXEMPLE, BASCULE, appliquer=True, debut_exercice=DEBUT, dossier="AUTRE")
        self.assertIn("ne peut pas y être mélangé", autre.texte())
        reprise_sage.basculer()
        self.assertEqual(Societe.get().source_mode, Societe.SYNCHRO_BASCULE)
        self.assertIn("synchronisation est arrêtée", self.importer().texte())
        Document.objects.get(numero="BC0001").transformer(Document.LIVRAISON)     # la saisie est ouverte dans l'ERP
        self.assertTrue(simulation.conforme)

    def test_synchronisation_incrementale(self):
        """Après un premier passage, on continue de travailler dans l'ancien logiciel ; le passage suivant reporte
        exactement les créations, modifications, transformations et suppressions."""
        import csv
        import shutil
        import tempfile

        self.assertTrue(self.importer().conforme)
        dossier = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, dossier)
        for f in EXEMPLE.glob("*.csv"):
            shutil.copy(f, dossier)

        def lire(nom):
            with open(dossier / f"{nom}.csv", encoding="utf-8") as f:
                return list(csv.DictReader(f, delimiter=";"))

        def ecrire(nom, lignes):
            with open(dossier / f"{nom}.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(lignes[0]), delimiter=";")
                w.writeheader()
                w.writerows(lignes)

        ecritures = [e for e in lire("ecritures") if e["EC_Piece"] != "AV1"]          # pièce supprimée à l'origine
        for e in ecritures:
            if e["EC_Piece"] == "RG2":
                e["EC_Intitule"] = "Acompte CL001 (corrigé)"                          # libellé modifié
        modele = next(e for e in ecritures if e["EC_Piece"] == "FA003")
        for no, compte, tiers, sens, montant in (("40", "411100", "CL002", "0", "11925"), ("41", "701100", "", "1", "10000"),
                                                 ("42", "443100", "", "1", "1925")):
            ecritures.append({**modele, "EC_No": no, "EC_Piece": "FA004", "EC_DateCompta": "2026-10-30", "CG_Num": compte,
                              "CT_Num": tiers, "EC_Sens": sens, "EC_Montant": montant, "EC_Intitule": "Facture FA004"})
        ecrire("ecritures", ecritures)
        documents = [d for d in lire("documents") if d["DO_Piece"] != "BC0001"]       # commande transformée en BL
        documents.append({**next(d for d in documents if d["DO_Piece"] == "FA003"), "DO_Piece": "FA004", "DO_Date": "2026-10-30"})
        documents.append({**next(d for d in documents if d["DO_Piece"] == "BL0001"), "DO_Piece": "BL0002",
                          "DO_Tiers": "CL001", "CT_NumPayeur": "CL001"})
        ecrire("documents", documents)
        lignes = lire("lignes")
        lignes.append({**next(l for l in lignes if l["DO_Piece"] == "FA003"), "DO_Piece": "FA004", "DL_No": "40",
                       "DL_Qte": "1", "DL_MontantHT": "10000", "DL_MontantTTC": "11925"})
        lignes.append({**next(l for l in lignes if l["DO_Piece"] == "BC0001"), "DO_Type": "3", "DO_Piece": "BL0002", "DL_No": "41"})
        ecrire("lignes", lignes)
        echeances = lire("echeances")
        echeances.append({**next(e for e in echeances if e["DO_Piece"] == "FA003"), "DR_No": "40", "DO_Piece": "FA004",
                          "DR_Montant": "11925"})
        ecrire("echeances", echeances)
        ecrire("reglements", [{**lire("reglements")[0], "RG_Impute": "1"}])            # versement imputé depuis
        ecrire("imputations", lire("imputations") + [{"RG_No": "3", "DR_No": "3", "RC_Montant": "30000"}])

        rapport = reprise_sage.importer(dossier, BASCULE, appliquer=True, debut_exercice=DEBUT, dossier=str(EXEMPLE))
        self.assertTrue(rapport.conforme, rapport.texte())
        b = rapport.bilans["ecritures"]
        self.assertEqual((b.creees, b.mises_a_jour, b.supprimees), (1, 1, 1))
        self.assertFalse(Ecriture.objects.filter(reference="AV1").exists())
        self.assertEqual(Ecriture.objects.get(reference="RG2").libelle, "Acompte CL001 (corrigé)")
        self.assertEqual(Document.objects.get(numero="FA004").reste_a_payer, Decimal("11925"))
        self.assertEqual(Document.objects.get(numero="BC0001").statut, Document.TRANSFORME)
        self.assertTrue(Document.objects.filter(numero="BL0002", type_document=Document.LIVRAISON).exists())
        self.assertEqual(Document.objects.get(numero="FA003").reste_a_payer, Decimal("29625"))
        self.assertFalse(Reglement.objects.filter(numero="RS-3").exists())             # imputé à l'origine : plus en attente
        self.assertEqual(Tiers.objects.get(code="CL002").solde_comptable(), Decimal("17700") + Decimal("11925"))


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
        self.assertContains(reponse, "Opération impossible")
        self.assertFalse(Document.objects.exclude(reprise_sage="").exists())

    def test_ecran_en_copie_synchronisee_puis_bascule(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        from apps.core.models import Societe

        self.assertTrue(reprise_sage.importer(EXEMPLE, BASCULE, appliquer=True, debut_exercice=DEBUT).conforme)
        url = reverse("commercial:reprise_dossier") + "?seul=1"
        self.client.force_login(get_user_model().objects.create_superuser("admin", "", "x"))
        page = self.client.get(url)
        self.assertContains(page, "Copie synchronisée")                         # bandeau et badge de la barre du haut
        self.assertContains(page, "Terminer la bascule")
        self.assertContains(page, "Derniers passages")
        self.assertNotContains(page, "Sage")
        self.client.post(url, {"action": "basculer", "confirmation_bascule": "non"})
        self.assertEqual(Societe.get().source_mode, Societe.SYNCHRO_MIROIR)    # confirmation exigée
        self.client.post(url, {"action": "basculer", "confirmation_bascule": "BASCULER"})
        self.assertEqual(Societe.get().source_mode, Societe.SYNCHRO_BASCULE)
        page = self.client.get(url)
        self.assertContains(page, "Bascule effectuée")
        self.assertNotContains(page, "Terminer la bascule")

    def test_synchronisation_planifiee(self):
        import os
        from io import StringIO
        from unittest import mock

        from django.core.management.base import CommandError

        sortie = StringIO()
        call_command("synchroniser_dossier", stdout=sortie)                     # rien à faire avant la première synchro
        self.assertIn("rien à faire", sortie.getvalue())
        self.assertTrue(reprise_sage.importer(EXEMPLE, BASCULE, appliquer=True, debut_exercice=DEBUT).conforme)
        with mock.patch.dict(os.environ, {"SYNCHRO_SERVEUR": "", "SYNCHRO_BASE": ""}):
            with self.assertRaisesMessage(CommandError, "SYNCHRO_SERVEUR"):
                call_command("synchroniser_dossier", stdout=StringIO())
