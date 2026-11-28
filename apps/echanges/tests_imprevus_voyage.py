"""Copies d'imprévus, frais, révisions et répartition du port dû entre agences."""
import copy
import datetime
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest import mock

from django.db import close_old_connections, connections, transaction
from django.test import TestCase, TransactionTestCase, SimpleTestCase, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone

from apps.comptabilite.models import Compte, Ecriture
from apps.comptabilite.services import creer_ecriture
from apps.core.models import Exercice
from apps.transport.models import Depart, Ligne, Vehicule
from apps.transport.models_incidents import Incident, FraisIncident
from . import contrats, publication, scenario_imprevus
from .models import Evenement
from .publication import import_en_cours, site_local
from .tests_incidents_colis import DonneesIncidents


class DonneesVoyages(DonneesIncidents):
    @classmethod
    def preparer_voyages(cls):
        cls.preparer()
        cls.date = Exercice.objects.first().date_debut + datetime.timedelta(days=10)
        cls.ligne = Ligne.objects.create(code="IV-AB", gare_depart=cls.gd, gare_arrivee=cls.ga, prix_billet=6000)
        cls.car = Vehicule.objects.create(immatriculation="IV-INITIAL", nombre_places=40)
        cls.secours = Vehicule.objects.create(immatriculation="IV-SECOURS", nombre_places=40)
        cls.charge = Compte.objects.get_or_create(numero="6240000", defaults={"intitule": "Entretien fictif"})[0]
        creer_ecriture(cls.caisse, cls.date, "Apport fictif", [
            {"compte": cls.caisse.compte_tresorerie, "debit": 10000},
            {"compte": Compte.objects.get(numero="1010000"), "credit": 10000}])

    def preparer_imprevu(self):
        self.depart = Depart.objects.create(ligne=self.ligne, vehicule=self.car, date=self.date,
                    heure=datetime.time(7), statut=Depart.PARTI, site_origine="DLA")
        self.p = {"v": 1, "uid": str(uuid.uuid4()), "numero": "DLA-INC-FICTIF", "depart": str(self.depart.uid),
                  "type_incident": Incident.TRANSBORDEMENT, "date": self.date.isoformat(), "lieu": "Étape fictive",
                  "description": "Panne fictive", "vehicule_secours": str(self.secours.uid), "part_restante": "40",
                  "cree_le": timezone.now().isoformat(), "auteur": "Agent source fictif", "auteur_id": self.admin.pk,
                  "ecriture": None, "numero_ecriture": "", "frais": []}

    def recevoir_voyage(self, p=None, revision=1, origine=None, local=None):
        p = p or self.p
        try:
            with transaction.atomic(), import_en_cours():
                contrats.INTEGRATIONS["incident_voyage"](p, origine or self.origine, local or site_local(), revision=revision)
        except contrats.SansObjet:
            pass
        return Incident.objects.get(uid=p["uid"])

    def frais_payload(self):
        return {"id": 1, "nature": FraisIncident.DEPANNAGE, "paiement": FraisIncident.CAISSE,
                "libelle": "Remorquage fictif", "montant": "1000", "compte": "6240000", "vehicule": None,
                "fournisseur": "", "ecriture": None, "numero_ecriture": ""}


class ImprevusEchangesTests(DonneesVoyages, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.preparer_voyages()

    def setUp(self):
        self.preparer_imprevu()

    def localiser(self):
        self.depart.site_origine = ""
        self.depart.save(update_fields=["site_origine"])

    def test_publication_des_frais_conserve_la_reference_comptable_finale(self):
        self.localiser()
        i = Incident.transborder(self.depart, 40, self.secours, utilisateur=self.admin)
        f = FraisIncident(incident=i, nature=FraisIncident.DEPANNAGE, montant=1000, libelle="Frais fictifs",
                          compte=self.charge, caisse=self.caisse).enregistrer()
        evts = Evenement.objects.filter(type="incident_voyage", objet_uid=i.uid).order_by("revision")
        self.assertEqual(evts.count(), 3)
        self.assertEqual(evts.last().payload["frais"][0]["ecriture"], str(f.ecriture.uid))
        self.assertEqual(evts.last().payload["auteur_id"], self.admin.pk)

    def test_reception_et_rejeu_ne_rejouent_ni_transbordement_ni_frais(self):
        self.p["frais"] = [self.frais_payload()]
        n, ne = Ecriture.objects.count(), Evenement.objects.count()
        with (mock.patch.object(Incident, "transborder", side_effect=AssertionError("Pas de rejeu")),
              mock.patch.object(FraisIncident, "enregistrer", side_effect=AssertionError("Pas de décaissement"))):
            self.recevoir_voyage()
            i = self.recevoir_voyage()
        self.assertEqual((Incident.objects.count(), FraisIncident.objects.count(), Ecriture.objects.count()), (1, 0, n))
        self.assertEqual(Evenement.objects.count(), ne)
        self.assertEqual((i.site_origine, i.part_restante, i.cree_par_id), ("DLA", 40, None))
        self.assertEqual(i.trace_origine["auteur_id"], self.admin.pk)

    def test_dependencies_absentes_attendent_sans_copie_partielle(self):
        for champ in ("depart", "vehicule_secours"):
            p = copy.deepcopy(self.p)
            p[champ] = str(uuid.uuid4())
            with self.subTest(champ=champ), self.assertRaises(contrats.Attente):
                self.recevoir_voyage(p)
        self.assertFalse(Incident.objects.exists())

    def test_autre_origine_refusee(self):
        with self.assertRaises(contrats.Conflit):
            self.recevoir_voyage(origine=self.destination)
        self.assertFalse(Incident.objects.exists())

    def test_ancienne_revision_ne_reecrit_pas_le_pourcentage(self):
        self.recevoir_voyage(revision=2)
        ancien = copy.deepcopy(self.p)
        ancien["part_restante"] = "20"
        i = self.recevoir_voyage(ancien, revision=1)
        self.assertEqual((i.part_restante, i.trace_origine["revision"]), (40, 2))

    def test_frais_paye_attend_sa_reference_au_siege_seulement(self):
        f = self.frais_payload()
        f.update(ecriture=str(uuid.uuid4()), numero_ecriture="CA-DLA-FICTIF")
        self.p["frais"] = [f]
        with self.assertRaises(contrats.Attente):
            self.recevoir_voyage()
        self.assertFalse(Incident.objects.exists())
        i = self.recevoir_voyage(local=self.destination)
        self.assertEqual(i.trace_origine["frais"][0]["ecriture"], f["ecriture"])
        self.assertFalse(FraisIncident.objects.exists())

    def test_frais_invalides_refuses(self):
        for montant in ("NaN", "Infinity", "-1", "1.5"):
            p = copy.deepcopy(self.p)
            f = self.frais_payload()
            f["montant"] = montant
            p["frais"] = [f]
            with self.subTest(montant=montant), self.assertRaises(contrats.Conflit):
                self.recevoir_voyage(p)
        self.assertFalse(Incident.objects.exists())

    def test_creation_et_publication_atomiques_meme_hors_service(self):
        self.localiser()
        publier = publication.publier
        def panne(*args, **kwargs):
            publier(*args, **kwargs)
            raise OSError("Panne fictive après publication réelle")
        with mock.patch.object(publication, "publier", side_effect=panne), self.assertRaises(OSError):
            Incident.objects.create(depart=self.depart, type_incident=Incident.RETARD, date=self.date)
        self.assertFalse(Incident.objects.exists())
        self.assertFalse(Evenement.objects.filter(type="incident_voyage").exists())

    def test_fenetre_distante_affiche_les_frais_sans_action_de_paiement(self):
        self.p["frais"] = [self.frais_payload()]
        self.recevoir_voyage()
        self.client.force_login(self.admin)
        page = self.client.get(reverse("transport:depart_detail", args=[self.depart.pk]))
        self.assertContains(page, "Imprévu transmis par DLA, en lecture seule")
        self.assertContains(page, "Remorquage fictif")
        self.assertNotContains(page, 'value="frais"')
        self.assertNotContains(page, 'value="recette_bord"')


@skipUnlessDBFeature("has_select_for_update")
class ImprevusImportsConcurrentsTests(DonneesVoyages, TransactionTestCase):
    def setUp(self):
        self.preparer_voyages()
        self.preparer_imprevu()

    def test_revisions_concurrentes_conservent_la_plus_recente(self):
        ancien, recent = copy.deepcopy(self.p), copy.deepcopy(self.p)
        ancien["part_restante"] = "20"
        barriere = Barrier(2, timeout=20)
        def travail(revision, payload):
            close_old_connections()
            try:
                connexion = connections["default"]
                with connexion.cursor() as curseur:
                    if connexion.vendor in ("microsoft", "mssql"):
                        curseur.execute("SET LOCK_TIMEOUT 15000")
                    elif connexion.vendor == "postgresql":
                        curseur.execute("SET lock_timeout = '15s'")
                barriere.wait()
                self.recevoir_voyage(payload, revision=revision)
            finally:
                connections["default"].close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futurs = [pool.submit(travail, 1, ancien), pool.submit(travail, 2, recent)]
            for futur in futurs:
                futur.result(timeout=45)
        i = Incident.objects.get()
        self.assertEqual((i.part_restante, i.trace_origine["revision"]), (40, 2))
        self.assertFalse(FraisIncident.objects.exists())


class ImprevusTroisDossiersTests(SimpleTestCase):
    def test_port_du_apres_transvasement_et_frais_sans_double_ecriture(self):
        with tempfile.TemporaryDirectory(prefix="erp-imprevus-fictifs-") as dossier:
            r = scenario_imprevus.executer(dossier)
        attendu = {"REPRO-INITIAL": Decimal("1500"), "REPRO-SECOURS": Decimal("1000")}
        self.assertEqual({k: Decimal(v) for k, v in r["destination"]["credits"].items()}, attendu)
        self.assertEqual({k: Decimal(v) for k, v in r["central"]["credits"].items()}, attendu)
        self.assertEqual((r["destination"]["ecritures"], r["central"]["ecritures"]), (1, 3))
        for lieu in ("destination", "central"):
            self.assertEqual((r[lieu]["imprevus"], r[lieu]["frais_locaux"]), (1, 0))
            self.assertEqual(len(r[lieu]["trace"]["frais"]), 1)
        self.assertIsNone(r["destination"]["auteur_local"])
        self.assertEqual(Decimal(r["central"]["depannage"]), Decimal("1000"))
