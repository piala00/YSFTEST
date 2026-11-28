"""Argent fictif : un reçu ne s'encaisse qu'une fois, ses imputations restent bornées."""
import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import close_old_connections, connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature

from apps.comptabilite.models import Ecriture, Journal
from apps.core.models import Agence, Exercice
from apps.echanges import publication
from apps.echanges.models import Evenement

from .models import Article, Document, LigneDocument, Reglement, Tiers


class DonneesReglements:
    @classmethod
    def preparer(cls):
        call_command("init_erp", verbosity=0)
        cls.date = Exercice.objects.first().date_debut + datetime.timedelta(days=10)
        Agence.objects.update(locale=False)
        Agence.objects.create(code="REGP0", nom="Agence fictive règlements", locale=True, uid=uuid.uuid4())
        cls.client_fictif = Tiers.objects.create(code="REG-C", nom="Client fictif")
        cls.article = Article.objects.create(reference="REG-A", designation="Service fictif", suivi_stock=False)
        cls.caisse = Journal.objects.get(code="CA")

    def facture(self):
        doc = Document.objects.create(type_document=Document.FACTURE, tiers=self.client_fictif, date=self.date)
        LigneDocument.objects.create(document=doc, article=self.article, quantite=1, prix_unitaire=10000, taux_tva=0)
        return doc.valider()

    def recu(self, montant=10000, comptabilise=True):
        recu = Reglement.objects.create(tiers=self.client_fictif, journal=self.caisse, date=self.date, montant=montant)
        return recu.enregistrer(en_attente=True) if comptabilise else recu


class ReglementsP0Tests(DonneesReglements, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.preparer()

    def test_ancien_recu_ne_produit_pas_un_second_encaissement(self):
        recu = self.recu(comptabilise=False)
        ancien = Reglement.objects.get(pk=recu.pk)
        recu.enregistrer(en_attente=True)
        numero, ecriture = recu.numero, recu.ecriture_id
        refuse = False
        try:
            ancien.enregistrer(en_attente=True)
        except ValidationError:
            refuse = True
        recu.refresh_from_db()
        self.assertEqual(Ecriture.objects.count(), 1)
        self.assertEqual((recu.numero, recu.ecriture_id), (numero, ecriture))
        self.assertEqual(Evenement.objects.filter(type="ecriture").count(), 1)
        self.assertTrue(refuse)

    def test_recu_comptabilise_ne_se_reecrit_pas_depuis_la_memoire(self):
        recu = self.recu()
        recu.montant = 90000
        with self.assertRaises(ValidationError):
            recu.enregistrer(en_attente=True)
        recu.refresh_from_db()
        self.assertEqual(recu.montant, 10000)
        self.assertEqual(Ecriture.objects.count(), 1)

    def test_rattachement_utilise_le_montant_stocke_du_recu(self):
        facture = self.facture()
        recu = self.recu(5000)
        recu.montant = 20000
        with self.assertRaises(ValidationError):
            recu.rattacher(facture, 8000)
        self.assertEqual(facture.montant_regle, 0)
        self.assertEqual(Reglement.objects.get(pk=recu.pk).en_attente_de_rattachement, 5000)

    def test_rattachement_utilise_le_reste_stocke_de_la_facture(self):
        facture = self.facture()
        recu = self.recu(20000)
        facture.total_ttc = Decimal("50000")
        with self.assertRaises(ValidationError):
            recu.rattacher(facture, 15000)
        self.assertEqual(Document.objects.get(pk=facture.pk).montant_regle, 0)

    def test_rattachement_reverifie_le_client_stocke(self):
        facture = self.facture()
        autre = Tiers.objects.create(code="REG-AUTRE", nom="Autre client fictif")
        recu = Reglement(tiers=autre, journal=self.caisse, date=self.date, montant=5000).enregistrer(en_attente=True)
        facture.tiers = autre  # une instance fournie ne fait pas foi sur la propriété de la facture
        with self.assertRaises(ValidationError):
            recu.rattacher(facture)
        self.assertEqual(facture.montant_regle, 0)

    def test_enregistrement_reverifie_la_facture_fournie(self):
        facture = self.facture()
        autre = Tiers.objects.create(code="REG-FAUX", nom="Client fictif sans facture")
        facture.tiers = autre
        recu = Reglement(tiers=autre, journal=self.caisse, date=self.date, montant=5000)
        with self.assertRaises(ValidationError):
            recu.enregistrer([facture])
        self.assertFalse(Reglement.objects.filter(tiers=autre).exists())

    def test_copie_miroir_refusee_avant_encaissement_ou_imputation(self):
        facture = self.facture()
        recu = self.recu()
        recu._state.db = "miroir"
        for action in (lambda: recu.enregistrer(en_attente=True), lambda: recu.rattacher(facture)):
            with self.subTest(action=action), self.assertRaisesMessage(ValidationError, "lecture"):
                action()
        self.assertEqual(Ecriture.objects.count(), 2)
        self.assertEqual(facture.montant_regle, 0)

    def test_recu_supprime_ne_peut_pas_etre_recree_par_un_ancien_objet(self):
        recu = self.recu(comptabilise=False)
        pk = recu.pk
        Reglement.objects.filter(pk=pk).delete()
        with self.assertRaisesMessage(ValidationError, "n'existe plus"):
            recu.enregistrer(en_attente=True)
        self.assertFalse(Reglement.objects.filter(pk=pk).exists())
        self.assertFalse(Ecriture.objects.exists())

    def test_panne_publication_annule_tout_et_reprise_du_meme_recu(self):
        recu = self.recu(comptabilise=False)
        publier = publication.publier_ecriture
        def panne(ecriture):
            publier(ecriture)
            raise OSError("Panne fictive après publication réelle")
        with mock.patch.object(publication, "publier_ecriture", side_effect=panne), self.assertRaises(OSError):
            recu.enregistrer(en_attente=True)
        self.assertIsNone(Reglement.objects.get(pk=recu.pk).ecriture_id)
        self.assertFalse(Ecriture.objects.exists())
        self.assertFalse(Evenement.objects.filter(type="ecriture").exists())
        recu.enregistrer(en_attente=True)
        recu.refresh_from_db()
        self.assertIsNotNone(recu.ecriture_id)
        self.assertEqual(Ecriture.objects.count(), 1)
        self.assertEqual(Evenement.objects.filter(type="ecriture").count(), 1)


@skipUnlessDBFeature("has_select_for_update")
class ReglementsConcurrentsP0Tests(DonneesReglements, TransactionTestCase):
    def setUp(self):
        self.preparer()

    def deux_actions(self, actions):
        barriere = Barrier(2, timeout=20)
        def travail(action):
            close_old_connections()
            try:
                connexion = connections["default"]
                with connexion.cursor() as curseur:
                    if connexion.vendor in ("microsoft", "mssql"):
                        curseur.execute("SET LOCK_TIMEOUT 15000")
                    elif connexion.vendor == "postgresql":
                        curseur.execute("SET lock_timeout = '15s'")
                recu = Reglement.objects.get(pk=action[0])
                facture = Document.objects.get(pk=action[1]) if len(action) > 1 else None
                barriere.wait()
                try:
                    recu.rattacher(facture, 8000) if facture else recu.enregistrer(en_attente=True)
                    return "ok"
                except ValidationError:
                    return "refus"
            finally:
                connections["default"].close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futurs = [pool.submit(travail, action) for action in actions]
            return [f.result(timeout=45) for f in futurs]

    def test_deux_encaissements_du_meme_recu_une_seule_ecriture(self):
        recu = self.recu(comptabilise=False)
        self.assertEqual(sorted(self.deux_actions([(recu.pk,), (recu.pk,)])), ["ok", "refus"])
        self.assertEqual((Reglement.objects.count(), Ecriture.objects.count()), (1, 1))
        self.assertEqual(Evenement.objects.filter(type="ecriture").count(), 1)

    def test_un_recu_ne_peut_pas_etre_impute_deux_fois_au_dela_de_son_montant(self):
        f1, f2 = self.facture(), self.facture()
        recu = self.recu()
        nombre = Ecriture.objects.count()
        self.assertEqual(sorted(self.deux_actions([(recu.pk, f1.pk), (recu.pk, f2.pk)])), ["ok", "refus"])
        self.assertEqual(recu.montant_impute, 8000)
        self.assertEqual(Ecriture.objects.count(), nombre)  # rattacher ne réencaisse rien

    def test_deux_recus_ne_soldent_pas_la_meme_facture_deux_fois(self):
        facture = self.facture()
        r1, r2 = self.recu(8000), self.recu(8000)
        nombre = Ecriture.objects.count()
        self.assertEqual(sorted(self.deux_actions([(r1.pk, facture.pk), (r2.pk, facture.pk)])), ["ok", "refus"])
        self.assertEqual(facture.montant_regle, 8000)
        self.assertEqual(Ecriture.objects.count(), nombre)
