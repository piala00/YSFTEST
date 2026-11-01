"""Documents fictifs : actions répétées, cache périmé, stock, comptabilité et reprise après panne."""
import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import close_old_connections, connections
from django.test import Client, TestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone

from apps.comptabilite.models import Ecriture
from apps.core import droits
from apps.core.models import Agence, DroitAcces, Exercice
from apps.echanges import publication
from apps.echanges.models import Evenement

from .models import Article, Depot, Document, LigneDocument, StockDepot, Tiers


class DonneesDocuments:
    @classmethod
    def preparer(cls):
        call_command("init_erp", verbosity=0)
        cls.date = Exercice.objects.first().date_debut + datetime.timedelta(days=10)
        Agence.objects.update(locale=False)
        Agence.objects.create(code="DOCS", nom="Agence fictive documents", locale=True, uid=uuid.uuid4())
        cls.client_fictif = Tiers.objects.create(code="DOC-C", nom="Client fictif")
        cls.fournisseur = Tiers.objects.create(code="DOC-F", nom="Fournisseur fictif", type_tiers=Tiers.FOURNISSEUR)
        cls.article = Article.objects.create(reference="DOC-A", designation="Article fictif", prix_achat=800, prix_vente=1000)
        cls.depot = Depot.par_defaut()
        stock = Document.objects.create(type_document=Document.STOCK_ENTREE, date=cls.date, depot=cls.depot)
        LigneDocument.objects.create(document=stock, article=cls.article, quantite=100, prix_unitaire=800)
        stock.valider()

    def document(self, genre=Document.FACTURE):
        tiers = self.fournisseur if genre in Document.TYPES_ACHAT else self.client_fictif
        doc = Document.objects.create(type_document=genre, tiers=tiers, date=self.date, depot=self.depot)
        LigneDocument.objects.create(document=doc, article=self.article, quantite=10, prix_unitaire=1000)
        doc.recalculer()
        return doc

    def stock(self):
        return StockDepot.quantite_de(self.article.pk, self.depot.pk)


class DocumentsP0Tests(DonneesDocuments, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.preparer()
        cls.admin = get_user_model().objects.create_superuser("documents-p0", "", "Fictif-2026-Recette")
        cls.lecteur = get_user_model().objects.create_user("documents-lecture", password="Fictif-2026-Recette")
        groupe = Group.objects.create(name="Documents consultation fictive")
        cls.lecteur.groups.add(groupe)
        DroitAcces.objects.create(groupe=groupe, module="commercial", code="ventes.facture", niveau=droits.LECTURE)

    def verifier_double_validation(self, genre, stock_attendu):
        doc = self.document(genre)
        ancien = Document.objects.get(pk=doc.pk)
        nombre = Ecriture.objects.count()
        doc.valider()
        numero, ecriture = doc.numero, doc.ecriture_id
        refuse = False
        try:
            ancien.valider()
        except ValidationError:
            refuse = True
        doc.refresh_from_db()
        with self.subTest(controle="stock"):
            self.assertEqual(self.stock(), stock_attendu)
        with self.subTest(controle="comptabilite"):
            self.assertEqual(Ecriture.objects.count(), nombre + 1)
            self.assertEqual(Evenement.objects.filter(type="ecriture").count(), 1)
        with self.subTest(controle="piece"):
            self.assertEqual((doc.numero, doc.ecriture_id), (numero, ecriture))
        self.assertTrue(refuse, "La seconde validation doit être refusée comme une validation répétée normale.")

    def test_double_validation_vente_ne_double_ni_stock_ni_ecriture(self):
        self.verifier_double_validation(Document.FACTURE, 90)

    def test_double_validation_achat_ne_double_ni_stock_ni_ecriture(self):
        self.verifier_double_validation(Document.ACHAT_FACTURE, 110)

    def test_facture_validee_inannulable_depuis_un_ancien_brouillon(self):
        doc = self.document()
        ancien = Document.objects.get(pk=doc.pk)
        doc.valider()
        with self.assertRaises(ValidationError):
            ancien.annuler()
        doc.refresh_from_db()
        self.assertEqual((doc.statut, self.stock(), doc.ecriture.statut),
                         (Document.VALIDE, 90, Ecriture.STATUT_VALIDEE))

    def test_annulation_livraison_depuis_ancien_brouillon_restitue_le_stock(self):
        doc = self.document(Document.LIVRAISON)
        ancien = Document.objects.get(pk=doc.pk)
        doc.valider()
        ancien.annuler()
        doc.refresh_from_db()
        self.assertEqual((doc.statut, self.stock(), doc.mouvements_stock.count()), (Document.ANNULE, 100, 0))

    def test_document_annule_non_revalide_par_un_ancien_objet(self):
        doc = self.document()
        ancien = Document.objects.get(pk=doc.pk)
        doc.annuler()
        with self.assertRaises(ValidationError):
            ancien.valider()
        doc.refresh_from_db()
        self.assertEqual((doc.statut, self.stock()), (Document.ANNULE, 100))
        self.assertFalse(Evenement.objects.filter(type="ecriture").exists())

    def test_validation_relit_la_reference_et_le_tiers_mis_a_jour(self):
        doc = self.document()
        ancien = Document.objects.select_related("tiers").get(pk=doc.pk)
        autre = Tiers.objects.create(code="DOC-C2", nom="Autre client fictif")
        Document.objects.filter(pk=doc.pk).update(tiers=autre, reference_externe="REF-CORRIGEE")
        ancien.valider()
        doc.refresh_from_db()
        self.assertEqual((doc.tiers_id, doc.reference_externe), (autre.pk, "REF-CORRIGEE"))
        self.assertEqual(doc.ecriture.reference, "REF-CORRIGEE")
        self.assertIn(autre.nom, doc.ecriture.libelle)

    def test_tiers_bloque_apres_chargement_de_la_piece_est_refuse(self):
        doc = self.document()
        ancien = Document.objects.select_related("tiers").get(pk=doc.pk)
        Tiers.objects.filter(pk=doc.tiers_id).update(compte_bloque=True)
        with self.assertRaises(ValidationError):
            ancien.valider()
        doc.refresh_from_db()
        self.assertEqual((doc.statut, self.stock()), (Document.BROUILLON, 100))

    def test_panne_apres_publication_annule_tout_et_reprise_du_meme_objet(self):
        doc = self.document()
        nombre = Ecriture.objects.count()
        publier = publication.publier_ecriture
        def panne(ecriture):
            publier(ecriture)
            raise OSError("Panne fictive après publication réelle")
        with mock.patch.object(publication, "publier_ecriture", side_effect=panne), self.assertRaises(OSError):
            doc.valider()
        courant = Document.objects.get(pk=doc.pk)
        self.assertEqual((courant.statut, courant.ecriture_id, self.stock()), (Document.BROUILLON, None, 100))
        self.assertEqual(Ecriture.objects.count(), nombre)
        self.assertEqual(courant.mouvements_stock.count(), 0)
        self.assertFalse(Evenement.objects.filter(type="ecriture").exists())
        doc.valider()  # le rollback SQL n'a pas rétabli le cache Python du premier appel.
        courant.refresh_from_db()
        self.assertEqual((courant.statut, self.stock()), (Document.VALIDE, 90))
        self.assertEqual(Ecriture.objects.count(), nombre + 1)
        self.assertEqual(Evenement.objects.filter(type="ecriture").count(), 1)

    def test_seconde_annulation_ne_reecrit_pas_la_trace_initiale(self):
        doc = self.document(Document.LIVRAISON)
        doc.valider()
        ancien = Document.objects.get(pk=doc.pk)
        instant = timezone.now()
        with mock.patch("apps.commercial.models.timezone.now", return_value=instant):
            doc.annuler()
        with mock.patch("apps.commercial.models.timezone.now", return_value=instant + datetime.timedelta(minutes=5)):
            ancien.annuler()
        doc.refresh_from_db()
        self.assertEqual((doc.annule_le, self.stock()), (instant, 100))

    def test_GET_ne_valide_et_ne_supprime_pas(self):
        self.client.force_login(self.admin)
        for nom in ("document_valider", "document_annuler"):
            with self.subTest(action=nom):
                doc = self.document()
                self.assertEqual(self.client.get(reverse("commercial:" + nom, args=[doc.pk])).status_code, 405)
                doc.refresh_from_db()
                self.assertEqual((doc.statut, self.stock()), (Document.BROUILLON, 100))

    def test_profil_lecture_refuse_validation_et_annulation(self):
        self.client.force_login(self.lecteur)
        for nom in ("document_valider", "document_annuler"):
            with self.subTest(action=nom):
                doc = self.document()
                self.assertEqual(self.client.post(reverse("commercial:" + nom, args=[doc.pk])).status_code, 403)
                doc.refresh_from_db()
                self.assertEqual((doc.statut, self.stock()), (Document.BROUILLON, 100))

    def test_POST_sans_CSRF_refuse_meme_un_administrateur(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        doc = self.document()
        for nom in ("document_valider", "document_annuler"):
            self.assertEqual(client.post(reverse("commercial:" + nom, args=[doc.pk])).status_code, 403)
        doc.refresh_from_db()
        self.assertEqual((doc.statut, self.stock()), (Document.BROUILLON, 100))

    def test_copie_miroir_non_modifiable_et_aucune_ecriture_sur_la_base_active(self):
        doc = self.document()
        for action in ("valider", "annuler"):
            with self.subTest(action=action), mock.patch.object(doc._state, "db", "miroir"):
                with self.assertRaisesMessage(ValidationError, "réservée à la lecture"):
                    getattr(doc, action)()
        doc.refresh_from_db()
        self.assertEqual((doc.statut, self.stock()), (Document.BROUILLON, 100))
        self.assertFalse(Ecriture.objects.exists())

    def test_document_supprime_entre_chargement_et_action_refuse_sans_mutation(self):
        doc = self.document()
        ancien = Document.objects.get(pk=doc.pk)
        doc.delete()
        for action in ("valider", "annuler"):
            with self.subTest(action=action), self.assertRaisesMessage(ValidationError, "n'existe plus"):
                getattr(ancien, action)()
        self.assertEqual(self.stock(), 100)
        self.assertFalse(Ecriture.objects.exists())


@skipUnlessDBFeature("has_select_for_update")
class DocumentsConcurrentsP0Tests(DonneesDocuments, TransactionTestCase):
    def setUp(self):
        self.preparer()

    def deux_actions(self, pk, action):
        # Même protocole que la recette comptable #22 : deux connexions, objets chargés avant la barrière.
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
                doc = Document.objects.get(pk=pk)
                barriere.wait()
                try:
                    getattr(doc, action)()
                    return "ok"
                except ValidationError:
                    return "refus"
            finally:
                connections["default"].close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futurs = [pool.submit(travail) for _ in range(2)]
            return [f.result(timeout=45) for f in futurs]

    def test_deux_validations_concurrentes_une_seule_piece_et_sortie_de_stock(self):
        doc = self.document()
        self.assertEqual(sorted(self.deux_actions(doc.pk, "valider")), ["ok", "refus"])
        self.assertEqual(self.stock(), 90)
        self.assertEqual(Ecriture.objects.count(), 1)
        self.assertEqual(Evenement.objects.filter(type="ecriture").count(), 1)
        self.assertEqual(doc.mouvements_stock.count(), 1)

    def test_deux_annulations_concurrentes_une_seule_restitution(self):
        doc = self.document(Document.LIVRAISON)
        doc.valider()
        self.assertEqual(self.deux_actions(doc.pk, "annuler"), ["ok", "ok"])
        doc.refresh_from_db()
        self.assertEqual((doc.statut, self.stock(), doc.mouvements_stock.count()), (Document.ANNULE, 100, 0))
