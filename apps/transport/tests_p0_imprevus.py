"""Frais fictifs : une pièce persistée ne doit décaisser qu'une fois."""
import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import close_old_connections, connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse

from apps.comptabilite.models import Compte, Ecriture, Journal
from apps.comptabilite.services import creer_ecriture
from apps.core.models import Agence, Exercice
from apps.echanges import publication
from apps.echanges.models import Evenement
from .models import Depart, Gare, Ligne, Vehicule
from .models_incidents import FraisIncident, Incident


class DonneesImprevusP0:
    @classmethod
    def preparer(cls):
        call_command("init_erp", activite="transport", verbosity=0)
        cls.date = Exercice.objects.first().date_debut + datetime.timedelta(days=10)
        Agence.objects.update(locale=False)
        Agence.objects.create(code="FRAISP0", nom="Agence fictive frais", locale=True, uid=uuid.uuid4())
        cls.a = Gare.objects.create(code="FP-A", nom="Départ fictif")
        cls.b = Gare.objects.create(code="FP-B", nom="Arrivée fictive")
        cls.ligne = Ligne.objects.create(code="FP-AB", gare_depart=cls.a, gare_arrivee=cls.b, prix_billet=6000)
        cls.car = Vehicule.objects.create(immatriculation="FRAIS-FICTIF", nombre_places=30)
        cls.caisse = Journal.objects.get(code="CA")
        cls.compte = Compte.objects.get_or_create(numero="6240000", defaults={"intitule": "Entretien fictif"})[0]
        capital = Compte.objects.get(numero="1010000")
        creer_ecriture(cls.caisse, cls.date, "Apport fictif", [
            {"compte": cls.caisse.compte_tresorerie, "debit": 10000}, {"compte": capital, "credit": 10000}])

    def preparer_voyage(self):
        self.depart = Depart.objects.create(ligne=self.ligne, vehicule=self.car, date=self.date,
                                            heure=datetime.time(7), statut=Depart.PARTI)
        self.incident = Incident.objects.create(depart=self.depart, type_incident=Incident.PANNE, date=self.date)

    def frais(self, persiste=False, montant=1000):
        f = FraisIncident(incident=self.incident, nature=FraisIncident.DEPANNAGE, libelle="Dépannage fictif",
                          montant=montant, compte=self.compte, caisse=self.caisse)
        if persiste:
            f.save()
        return f


class FraisImprevusP0Tests(DonneesImprevusP0, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.preparer()
        cls.admin = get_user_model().objects.create_superuser("frais-fictifs", "", "Fictif-2026")

    def setUp(self):
        self.preparer_voyage()

    def test_meme_frais_persistant_ne_cree_pas_deux_decaissements(self):
        frais = self.frais(persiste=True)
        ancien = FraisIncident.objects.get(pk=frais.pk)
        avant = Ecriture.objects.count()
        frais.enregistrer()
        ecriture = frais.ecriture_id
        refuse = False
        try:
            ancien.enregistrer()
        except ValidationError:
            refuse = True
        self.assertEqual(Ecriture.objects.count()-avant, 1)
        frais.refresh_from_db()
        self.assertEqual(frais.ecriture_id, ecriture)
        self.assertTrue(refuse)

    def test_frais_comptabilise_ne_reecrit_pas_le_montant_stocke(self):
        frais = self.frais().enregistrer()
        frais.montant = 9000
        with self.assertRaises(ValidationError):
            frais.enregistrer()
        frais.refresh_from_db()
        self.assertEqual(frais.montant, 1000)

    def test_frais_sur_depart_distant_refuse_sans_ecriture(self):
        Depart.objects.filter(pk=self.depart.pk).update(site_origine="DLA")
        n = Ecriture.objects.count()
        with self.assertRaises(ValidationError):
            self.frais().enregistrer()
        self.assertEqual(Ecriture.objects.count(), n)
        self.assertFalse(FraisIncident.objects.exists())

    def test_recette_a_bord_sur_depart_distant_refusee(self):
        Depart.objects.filter(pk=self.depart.pk).update(site_origine="DLA")
        n = Ecriture.objects.count()
        with self.assertRaises(ValidationError):
            Incident.recette_a_bord(self.depart, 1000, 1, self.caisse)
        self.assertEqual(Ecriture.objects.count(), n)

    def test_recette_a_bord_relit_le_statut_du_depart(self):
        Depart.objects.filter(pk=self.depart.pk).update(statut=Depart.ANNULE)
        n = Ecriture.objects.count()
        with self.assertRaises(ValidationError):
            Incident.recette_a_bord(self.depart, 1000, 1, self.caisse)
        self.assertEqual(Ecriture.objects.count(), n)

    def test_copies_miroir_refusees_avant_toute_saisie(self):
        frais = self.frais()
        frais._state.db = "miroir"
        with self.assertRaisesMessage(ValidationError, "lecture"):
            frais.enregistrer()
        self.depart._state.db = "miroir"
        with self.assertRaisesMessage(ValidationError, "lecture"):
            Incident.recette_a_bord(self.depart, 1000, 1, self.caisse)

    def test_montants_non_finis_nuls_negatifs_ou_fractionnaires_refuses(self):
        n = Ecriture.objects.count()
        for montant in ("NaN", "Infinity", "0", "-100", "1.5"):
            with self.subTest(montant=montant), self.assertRaises(ValidationError):
                self.frais(montant=Decimal(montant)).enregistrer()
        self.assertEqual(Ecriture.objects.count(), n)
        self.assertFalse(FraisIncident.objects.exists())

    def test_panne_publication_annule_le_frais_et_permet_la_reprise(self):
        frais = self.frais(persiste=True)
        n, ne = Ecriture.objects.count(), Evenement.objects.filter(type="ecriture").count()
        publier = publication.publier_ecriture
        def panne(ecriture):
            publier(ecriture)
            raise OSError("Panne fictive après publication réelle")
        with mock.patch.object(publication, "publier_ecriture", side_effect=panne), self.assertRaises(OSError):
            frais.enregistrer()
        frais.refresh_from_db()
        self.assertIsNone(frais.ecriture_id)
        self.assertEqual(Ecriture.objects.count(), n)
        self.assertEqual(Evenement.objects.filter(type="ecriture").count(), ne)
        frais.enregistrer()
        self.assertEqual(Ecriture.objects.count(), n+1)
        self.assertEqual(Evenement.objects.filter(type="ecriture").count(), ne+1)

    def test_post_frais_distant_ne_cree_meme_pas_un_imprevu_local(self):
        self.client.force_login(self.admin)
        Depart.objects.filter(pk=self.depart.pk).update(site_origine="DLA")
        n, ni = Ecriture.objects.count(), Incident.objects.count()
        self.client.post(reverse("transport:depart_detail", args=[self.depart.pk]),
                         {"action": "frais", "type_incident": "PANNE", "nature": "DEPANNAGE",
                          "montant": "1000", "caisse": self.caisse.pk, "libelle": "Dépannage fictif"})
        self.assertEqual((Ecriture.objects.count(), Incident.objects.count()), (n, ni))


@skipUnlessDBFeature("has_select_for_update")
class FraisConcurrentsP0Tests(DonneesImprevusP0, TransactionTestCase):
    def setUp(self):
        self.preparer()
        self.preparer_voyage()

    def test_deux_enregistrements_concurrents_un_seul_decaissement(self):
        frais = self.frais(persiste=True)
        avant = Ecriture.objects.count()
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
                courant = FraisIncident.objects.get(pk=frais.pk)
                barriere.wait()
                try:
                    courant.enregistrer()
                    return "ok"
                except ValidationError:
                    return "refus"
            finally:
                connections["default"].close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futurs = [pool.submit(travail) for _ in range(2)]
            resultats = [f.result(timeout=45) for f in futurs]
        self.assertEqual(sorted(resultats), ["ok", "refus"])
        self.assertEqual(Ecriture.objects.count()-avant, 1)
