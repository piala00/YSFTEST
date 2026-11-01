"""Une pièce de garage persistée ne doit produire qu'un effet financier et stock."""
import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import close_old_connections, connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature

from apps.commercial.models import Tiers
from apps.comptabilite.models import Compte, Ecriture, Journal
from apps.comptabilite.services import creer_ecriture
from apps.core.models import Agence, Exercice
from apps.echanges import publication
from apps.echanges.models import Evenement
from apps.transport.models import Vehicule

from .models import LigneReparation, OrdreReparation, PleinCarburant
from .models_magasin import AchatMagasin, ArticleMagasin, LigneAchatMagasin, MouvementMagasin


class DonneesGarageP0:
    @classmethod
    def preparer(cls):
        call_command("init_erp", activite="transport", verbosity=0)
        cls.date = Exercice.objects.first().date_debut + datetime.timedelta(days=10)
        Agence.objects.update(locale=False)
        Agence.objects.create(code="GARAGEP0", nom="Garage fictif", locale=True, uid=uuid.uuid4())
        cls.car = Vehicule.objects.create(immatriculation="GARAGE-FICTIF", nombre_places=30)
        cls.caisse = Journal.objects.get(code="CA")
        cls.fournisseur = Tiers.objects.create(code="GARP0", nom="Fournisseur fictif", type_tiers=Tiers.FOURNISSEUR)
        creer_ecriture(cls.caisse, cls.date, "Apport fictif garage", [
            {"compte": cls.caisse.compte_tresorerie, "debit": 100000},
            {"compte": Compte.objects.get(numero="1010000"), "credit": 100000}])

    def plein(self):
        return PleinCarburant.objects.create(numero="FICTIF-"+uuid.uuid4().hex[:12],
                                             vehicule=self.car, date=self.date, litres=10, prix_litre=100,
                                             montant=1000, caisse=self.caisse)

    def achat(self):
        article = ArticleMagasin.objects.create(code="ARTICLE-P0", designation="Pièce fictive")
        a = AchatMagasin.objects.create(date=self.date, paiement=AchatMagasin.COMPTE, fournisseur=self.fournisseur)
        LigneAchatMagasin.objects.create(achat=a, article=article, destination=LigneAchatMagasin.STOCK,
                                        quantite=10, prix_unitaire=1000)
        return a

    def ordre(self):
        a = self.achat().valider()
        article = a.lignes.get().article
        o = OrdreReparation.objects.create(vehicule=self.car, panne="Réparation fictive", date_entree=self.date)
        LigneReparation.objects.create(ordre=o, nature=LigneReparation.MAGASIN, article=article,
                                       designation="Pièce fictive du stock", quantite=2, prix_unitaire=1000)
        return o

    def executer(self, objet):
        if isinstance(objet, PleinCarburant):
            return objet.enregistrer()
        if isinstance(objet, AchatMagasin):
            return objet.valider()
        return objet.cloturer(caisse=self.caisse, date=self.date)


class ValidationGarageP0Tests(DonneesGarageP0, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.preparer()

    def test_plein_ancien_ne_decaisse_pas_deux_fois(self):
        plein = self.plein()
        ancien = PleinCarburant.objects.get(pk=plein.pk)
        n = Ecriture.objects.count()
        self.executer(plein)
        refuse = False
        try:
            self.executer(ancien)
        except ValidationError:
            refuse = True
        self.assertEqual(Ecriture.objects.count()-n, 1)
        self.assertTrue(refuse)

    def test_achat_ancien_ne_double_ni_stock_ni_dette(self):
        achat = self.achat()
        ancien = AchatMagasin.objects.get(pk=achat.pk)
        n = Ecriture.objects.count()
        self.executer(achat)
        refuse = False
        try:
            self.executer(ancien)
        except ValidationError:
            refuse = True
        self.assertEqual(Ecriture.objects.count()-n, 1)
        self.assertEqual(ArticleMagasin.objects.get(code="ARTICLE-P0").quantite, 10)
        self.assertEqual(achat.mouvements.count(), 1)
        self.assertTrue(refuse)

    def test_ordre_ancien_ne_sort_pas_deux_fois_la_piece(self):
        ordre = self.ordre()
        ancien = OrdreReparation.objects.get(pk=ordre.pk)
        n = Ecriture.objects.count()
        self.executer(ordre)
        refuse = False
        try:
            self.executer(ancien)
        except ValidationError:
            refuse = True
        self.assertEqual(Ecriture.objects.count()-n, 1)
        self.assertEqual(ArticleMagasin.objects.get(code="ARTICLE-P0").quantite, 8)
        self.assertEqual(ordre.sorties.count(), 1)
        self.assertTrue(refuse)

    def test_plein_comptabilise_ne_reecrit_pas_son_montant(self):
        plein = self.plein().enregistrer()
        plein.montant = 9000
        with self.assertRaises(ValidationError):
            plein.enregistrer()
        plein.refresh_from_db()
        self.assertEqual(plein.montant, 1000)

    def test_piece_supprimee_ne_ressuscite_pas(self):
        for fabrique in (self.plein, self.achat, self.ordre):
            # Chaque sous-cas possède son propre article fictif.
            if ArticleMagasin.objects.exists():
                ArticleMagasin.objects.all().update(code="ANCIEN-ARTICLE")
            objet = fabrique()
            type(objet).objects.filter(pk=objet.pk).delete()
            n = Ecriture.objects.count()
            with self.subTest(modele=type(objet).__name__), self.assertRaises(ValidationError):
                self.executer(objet)
            self.assertEqual(Ecriture.objects.count(), n)

    def test_copies_miroir_et_origine_distante_refusees(self):
        for objet in (self.plein(), self.achat(), OrdreReparation.objects.create(
                vehicule=self.car, panne="Fictif", date_entree=self.date)):
            objet._state.db = "miroir"
            n = Ecriture.objects.count()
            with self.subTest(modele=type(objet).__name__), self.assertRaisesMessage(ValidationError, "lecture"):
                self.executer(objet)
            self.assertEqual(Ecriture.objects.count(), n)
        for objet in (self.plein(), OrdreReparation.objects.create(vehicule=self.car, panne="Fictif", date_entree=self.date)):
            type(objet).objects.filter(pk=objet.pk).update(site_origine="DISTANT")
            n = Ecriture.objects.count()
            with self.subTest(origine=type(objet).__name__), self.assertRaises(ValidationError):
                self.executer(objet)
            self.assertEqual(Ecriture.objects.count(), n)

    def test_panne_publication_annule_stock_et_ecriture_puis_reprise_unique(self):
        achat = self.achat()
        n, ne = Ecriture.objects.count(), Evenement.objects.filter(type="ecriture").count()
        publier = publication.publier_ecriture
        def panne(ecriture):
            publier(ecriture)
            raise OSError("Panne fictive garage après publication réelle")
        with mock.patch.object(publication, "publier_ecriture", side_effect=panne), self.assertRaises(OSError):
            achat.valider()
        achat.refresh_from_db()
        self.assertEqual(achat.statut, AchatMagasin.BROUILLON)
        self.assertEqual(ArticleMagasin.objects.get(code="ARTICLE-P0").quantite, 0)
        self.assertFalse(MouvementMagasin.objects.filter(achat=achat).exists())
        self.assertEqual((Ecriture.objects.count(), Evenement.objects.filter(type="ecriture").count()), (n, ne))
        achat.valider()
        self.assertEqual(ArticleMagasin.objects.get(code="ARTICLE-P0").quantite, 10)
        self.assertEqual((Ecriture.objects.count(), Evenement.objects.filter(type="ecriture").count()), (n+1, ne+1))


@skipUnlessDBFeature("has_select_for_update")
class ValidationGarageConcurrenteP0Tests(DonneesGarageP0, TransactionTestCase):
    def setUp(self):
        self.preparer()

    def concurremment(self, objet):
        barriere = Barrier(2, timeout=20)
        def travail():
            close_old_connections()
            try:
                connexion = connections["default"]
                with connexion.cursor() as curseur:
                    if connexion.vendor in ("microsoft", "mssql"):
                        curseur.execute("SET LOCK_TIMEOUT 15000")
                    elif connexion.vendor == "postgresql":
                        curseur.execute("SET lock_timeout = '15s'")
                courant = type(objet).objects.get(pk=objet.pk)
                barriere.wait()
                try:
                    self.executer(courant)
                    return "ok"
                except ValidationError:
                    return "refus"
            finally:
                connections["default"].close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futurs = [pool.submit(travail) for _ in range(2)]
            resultats = [f.result(timeout=45) for f in futurs]
        self.assertEqual(sorted(resultats), ["ok", "refus"])

    def test_plein_concurrent_un_seul_decaissement(self):
        plein = self.plein()
        n = Ecriture.objects.count()
        self.concurremment(plein)
        self.assertEqual(Ecriture.objects.count()-n, 1)

    def test_achat_concurrent_un_seul_stock_et_une_dette(self):
        achat = self.achat()
        n = Ecriture.objects.count()
        self.concurremment(achat)
        self.assertEqual(Ecriture.objects.count()-n, 1)
        self.assertEqual(ArticleMagasin.objects.get(code="ARTICLE-P0").quantite, 10)
        self.assertEqual(achat.mouvements.count(), 1)

    def test_cloture_concurrente_une_seule_sortie_de_piece(self):
        ordre = self.ordre()
        n = Ecriture.objects.count()
        self.concurremment(ordre)
        self.assertEqual(Ecriture.objects.count()-n, 1)
        self.assertEqual(ArticleMagasin.objects.get(code="ARTICLE-P0").quantite, 8)
        self.assertEqual(ordre.sorties.count(), 1)
