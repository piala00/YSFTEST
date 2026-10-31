"""Suivi reçu : dépendances, copies en lecture et absence de nouveaux paiements."""
import copy
import tempfile
import uuid
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import transaction, close_old_connections, connections
from django.test import TestCase, SimpleTestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone

from apps.comptabilite.models import Compte, Ecriture, Journal
from apps.comptabilite.services import creer_ecriture
from apps.transport.models import Colis, Gare
from apps.transport.models_suivi_colis import IncidentColis

from . import contrats, lots
from .models import Evenement, EvenementRecu, LotRecu
from .publication import import_en_cours, site_local
from .scenario import Dossier, lots_de


class DonneesIncidents:
    @classmethod
    def preparer(cls):
        call_command("init_erp", activite="transport", verbosity=0)
        lots.configurer_siege("SIEGE", "Siège fictif")
        cls.origine = lots.ajouter_agence("DLA", "Douala fictif")
        cls.destination = lots.ajouter_agence("YDE", "Yaoundé fictif")
        cls.gd = Gare.objects.create(code="IC-D", nom="Départ fictif", agence=cls.origine)
        cls.ga = Gare.objects.create(code="IC-A", nom="Arrivée fictive", agence=cls.destination)
        cls.admin = get_user_model().objects.create_superuser("incidents-fictifs", "", "Fictif-local-2026")
        cls.caisse = Journal.objects.get(code="CA")
        cls.compte = Compte.objects.get_or_create(numero="6580000", defaults={"intitule": "Indemnités fictives"})[0]

    def preparer_payload(self):
        self.colis = Colis.objects.create(numero="IC-FICTIF", site_origine="DLA", gare_depart=self.gd,
                                          gare_arrivee=self.ga, expediteur="E fictif", destinataire="D fictif")
        self.payload = {"v": 1, "uid": str(uuid.uuid4()), "colis": str(self.colis.uid), "nature": "SANS_TRACE",
                        "lieu": "Quai fictif", "description": "Recherche fictive", "declare_le": timezone.now().isoformat(),
                        "resolu": False, "resolution": "", "resolu_le": None, "montant_autorise": "0",
                        "auteurs": {"declare_par": "Agent d'origine fictif"}, "compte": None, "ecriture": None,
                        "numero_ecriture": ""}

    def recevoir(self, payload=None, origine=None, local=None, revision=1):
        try:
            with transaction.atomic(), import_en_cours():
                contrats.INTEGRATIONS["incident_colis"](payload or self.payload, origine or self.origine,
                                                        local or site_local(), revision=revision)
        except contrats.SansObjet:
            pass  # doublon reconnu ; la copie déjà intégrée reste identique
        return IncidentColis.objects.get(uid=(payload or self.payload)["uid"])

    def paiement(self, uid):
        self.payload.update(montant_autorise="5000", compte={"numero": self.compte.numero, "intitule": self.compte.intitule},
                            ecriture=str(uid), numero_ecriture="CA-DLA-FICTIF")
        self.payload["auteurs"].update(autorise_par="Chef fictif", paye_par="Caissier fictif")


class EchangesIncidentsColisTests(DonneesIncidents, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.preparer()

    def setUp(self):
        self.preparer_payload()

    def test_declaration_et_resolution_locales_publiees_sans_ecriture(self):
        self.colis.site_origine = ""
        self.colis.save(update_fields=["site_origine"])
        n = Ecriture.objects.count()
        incident = IncidentColis.declarer(self.colis, "SANS_TRACE", "Quai", "Recherche", self.admin)
        incident.resoudre("Colis retrouvé fictif", self.admin)
        evenements = Evenement.objects.filter(type="incident_colis", objet_uid=incident.uid).order_by("revision")
        self.assertEqual(list(evenements.values_list("revision", flat=True)), [1, 2])
        self.assertEqual(evenements.last().payload["auteurs"]["resolu_par"], self.admin.username)
        self.assertEqual(evenements.last().payload["auteurs_ids"]["resolu_par"], self.admin.pk)
        self.assertEqual(Ecriture.objects.count(), n)

    def test_reception_et_rejeu_ne_creent_ni_ecriture_ni_evenement_sortant(self):
        n, ne = Ecriture.objects.count(), Evenement.objects.count()
        with mock.patch("apps.comptabilite.services.creer_ecriture", side_effect=AssertionError("Aucun paiement à rejouer")):
            self.recevoir()
            incident = self.recevoir()
        self.assertEqual((IncidentColis.objects.count(), Ecriture.objects.count(), Evenement.objects.count()), (1, n, ne))
        self.assertEqual(incident.site_origine, "DLA")
        self.assertEqual(incident.declare_le.isoformat(), self.payload["declare_le"])
        self.assertIsNone(incident.declare_par_id)
        self.assertEqual(incident.trace_origine["auteurs"], self.payload["auteurs"])

    def test_colis_manquant_attend_sans_creer_de_suivi(self):
        self.payload["colis"] = str(uuid.uuid4())
        with self.assertRaises(contrats.Attente):
            self.recevoir()
        self.assertFalse(IncidentColis.objects.exists())

    def test_autre_site_refuse_avant_copie(self):
        with self.assertRaises(contrats.Conflit):
            self.recevoir(origine=self.destination)
        self.assertFalse(IncidentColis.objects.exists())

    def test_copie_distante_refuse_resolution_autorisation_et_paiement(self):
        incident = self.recevoir()
        for action in (lambda: incident.resoudre("Retrouvé", self.admin),
                       lambda: incident.autoriser(5000, self.compte, self.admin),
                       lambda: incident.payer(self.caisse, self.admin)):
            with self.subTest(action=action), self.assertRaisesMessage(ValidationError, "seule cette agence"):
                action()
        incident.refresh_from_db()
        self.assertEqual((incident.resolu, incident.montant_autorise, incident.ecriture_id), (False, 0, None))

    def test_paiement_attend_son_ecriture_au_siege_mais_pas_dans_une_autre_agence(self):
        self.paiement(uuid.uuid4())
        with self.assertRaises(contrats.Attente):
            self.recevoir()
        self.assertFalse(IncidentColis.objects.exists())
        n = Ecriture.objects.count()
        incident = self.recevoir(local=self.destination)
        self.assertIsNone(incident.ecriture_id)
        self.assertEqual(incident.trace_origine["ecriture"], self.payload["ecriture"])
        self.assertEqual(Ecriture.objects.count(), n)

    def test_suivi_paye_se_lie_a_l_ecriture_recue_sans_la_recreer(self):
        capital = Compte.objects.get(numero="1010000")
        e = creer_ecriture(self.caisse, timezone.localdate(), "Fait fictif reçu", [
            {"compte": self.compte, "debit": 5000}, {"compte": capital, "credit": 5000}])
        Ecriture.objects.filter(pk=e.pk).update(site_origine="DLA")
        self.paiement(e.uid)
        n = Ecriture.objects.count()
        incident = self.recevoir()
        self.recevoir()
        self.assertEqual((incident.ecriture_id, Ecriture.objects.count()), (e.pk, n))

    def test_montants_invalides_refuses_avant_copie(self):
        for montant in ("NaN", "Infinity", "-1", "1.5"):
            p = copy.deepcopy(self.payload)
            p["montant_autorise"] = montant
            with self.subTest(montant=montant), self.assertRaises(contrats.Conflit):
                self.recevoir(p)
        self.assertFalse(IncidentColis.objects.exists())

    def test_fenetre_distante_en_lecture_seule_meme_pour_un_administrateur(self):
        self.recevoir()
        self.client.force_login(self.admin)
        page = self.client.get(reverse("transport:colis_detail", args=[self.colis.pk]))
        self.assertContains(page, "Suivi transmis par DLA, en lecture seule")
        self.assertContains(page, "Agent d&#x27;origine fictif")
        for action in ("resoudre_incident", "autoriser_indemnite", "payer_indemnite", "incident_colis"):
            self.assertNotContains(page, 'value="'+action+'"')

    def test_une_ancienne_revision_ne_rouvre_pas_le_suivi_resolu(self):
        p = copy.deepcopy(self.payload)
        p.update(resolu=True, resolution="Retrouvé fictif", resolu_le=timezone.now().isoformat())
        lot = LotRecu.objects.create(uid=uuid.uuid4(), source=self.origine, empreinte="0"*64, nom_fichier="fictif.erpx")
        def recevoir_revision(revision, payload):
            evt = EvenementRecu.objects.create(site_origine=self.origine, uid=uuid.uuid4(), sequence=100+revision,
                      type="incident_colis", objet_uid=p["uid"], revision=revision, operation="ENREGISTRE", payload=payload,
                      lot=lot, empreinte="1"*64)
            lots._integrer_en_attente(site_local(), lots.Rapport())
            evt.refresh_from_db()
            return evt
        self.assertEqual(recevoir_revision(2, p).statut, EvenementRecu.INTEGRE)
        self.assertEqual(recevoir_revision(1, self.payload).statut, EvenementRecu.IGNORE)
        self.assertTrue(IncidentColis.objects.get(uid=p["uid"]).resolu)

    def test_rattrapage_des_suivis_anterieurs_sans_doublon(self):
        self.colis.site_origine = ""
        self.colis.save(update_fields=["site_origine"])
        with mock.patch("apps.echanges.publication.publier_objet"):
            incident = IncidentColis.declarer(self.colis, "SANS_TRACE", "Quai", "Recherche", self.admin)
        self.assertFalse(Evenement.objects.filter(type="incident_colis").exists())
        lots.publier_existant()
        lots.publier_existant()
        self.assertEqual(Evenement.objects.filter(type="incident_colis", objet_uid=incident.uid).count(), 1)

    def test_panne_outbox_annule_la_resolution(self):
        self.colis.site_origine = ""
        self.colis.save(update_fields=["site_origine"])
        incident = IncidentColis.declarer(self.colis, "SANS_TRACE", "Quai", "Recherche", self.admin)
        with mock.patch("apps.echanges.publication.publier", side_effect=OSError("Panne fictive")), self.assertRaises(OSError):
            incident.resoudre("Retrouvé", self.admin)
        incident.refresh_from_db()
        self.assertFalse(incident.resolu)
        self.assertEqual(Evenement.objects.filter(type="incident_colis", objet_uid=incident.uid).count(), 1)


@skipUnlessDBFeature("has_select_for_update")
class IncidentsImportsConcurrentsTests(DonneesIncidents, TransactionTestCase):
    def setUp(self):
        self.preparer()
        self.preparer_payload()

    def test_deux_revisions_concurrentes_conservent_la_plus_recente(self):
        ancien, recent = copy.deepcopy(self.payload), copy.deepcopy(self.payload)
        recent.update(resolu=True, resolution="Retrouvé fictif", resolu_le=timezone.now().isoformat())
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
                self.recevoir(payload, revision=revision)
            finally:
                connections["default"].close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futurs = [pool.submit(travail, 1, ancien), pool.submit(travail, 2, recent)]
            for f in futurs:
                f.result(timeout=45)
        incident = IncidentColis.objects.get()
        self.assertTrue(incident.resolu)
        self.assertEqual(incident.trace_origine["revision"], 2)
        self.assertFalse(Ecriture.objects.exists())
        self.assertFalse(Evenement.objects.filter(type="incident_colis").exists())


class IncidentsTroisDossiersTests(SimpleTestCase):
    def test_lots_signes_desordonnes_siege_et_relais_sans_second_paiement(self):
        with tempfile.TemporaryDirectory(prefix="erp-incidents-fictifs-") as travail:
            siege, source, arrivee = (Dossier(travail, n) for n in ("siege", "douala", "yaounde"))
            for dossier in (siege, source, arrivee):
                dossier.creer()
            siege.manage("echanges", "siege", "--code", "SIEGE", "--nom", "Siège fictif")
            for code in ("DLA", "YDE"):
                siege.manage("echanges", "agence", "--code", code, "--nom", code + " fictif")
            siege.py('''
import json
from apps.core.models import Agence
from apps.transport.models import Gare
for code in ("DLA", "YDE"):
    Gare.objects.create(code=code,nom=code+" fictif",agence=Agence.objects.get(code=code))
print("null")''')
            for code, dossier in (("DLA", source), ("YDE", arrivee)):
                installation = lots_de(siege.manage("echanges", "installation", "--agence", code, "--dossier", travail))[0]
                dossier.manage("echanges", "installer", installation)
            source.py('''
import json
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.comptabilite.models import Compte,Journal
from apps.comptabilite.services import creer_ecriture
from apps.transport.models import Colis,Gare
from apps.transport.models_suivi_colis import IncidentColis
a=get_user_model().objects.create_superuser("agent-fictif","","Fictif-2026")
j=Journal.objects.get(code="CA")
creer_ecriture(j,timezone.localdate(),"Apport fictif",[
 {"compte":j.compte_tresorerie,"debit":100000},{"compte":Compte.objects.get(numero="1010000"),"credit":100000}])
c=Colis(gare_depart=Gare.objects.get(code="DLA"),gare_arrivee=Gare.objects.get(code="YDE"),
 expediteur="E fictif",destinataire="D fictif",prix=2500,port=Colis.DU).enregistrer(a)
IncidentColis.declarer(c,"SANS_TRACE","Quai fictif","Recherche fictive",a)
print("null")''')
            premier = lots_de(source.manage("echanges", "exporter", "--dossier", travail))[0]
            resultat_source = source.py('''
import json
from django.contrib.auth import get_user_model
from apps.comptabilite.models import Compte,Ecriture,Journal,LigneEcriture
from apps.transport.models_suivi_colis import IncidentColis
a=get_user_model().objects.get(username="agent-fictif")
c=Compte.objects.get_or_create(numero="6580000",defaults={"intitule":"Indemnités fictives"})[0]
i=IncidentColis.objects.get().autoriser(5000,c,a)
i=i.payer(Journal.objects.get(code="CA"),a)
i=i.resoudre("Retrouvé et dommage traité (fictif)",a)
print(json.dumps({"n_gl":Ecriture.objects.count(),"agent":a.pk,"ecriture":str(i.ecriture.uid)}))''')
            second = lots_de(source.manage("echanges", "exporter", "--dossier", travail))[0]
            siege.manage("echanges", "importer", second)
            attente = siege.py('''
import json
from apps.echanges.models import EvenementRecu
print(json.dumps(EvenementRecu.objects.filter(type="incident_colis",statut="ATTENTE").count()))''')
            self.assertGreater(attente, 0)
            siege.manage("echanges", "importer", premier)
            siege.manage("echanges", "importer", premier)
            rapport = '''
import json
from django.db.models import Sum
from apps.comptabilite.models import Ecriture,LigneEcriture
from apps.transport.models_suivi_colis import IncidentColis
i=IncidentColis.objects.get()
print(json.dumps({"n_gl":Ecriture.objects.count(),"n_incidents":IncidentColis.objects.count(),
 "resolu":i.resolu,"origine":i.site_origine,"ecriture_liee":i.ecriture_id is not None,
 "trace":i.trace_origine,"indemnite":str(LigneEcriture.objects.filter(compte__numero="6580000").aggregate(s=Sum("debit"))["s"] or 0)}))'''
            central = siege.py(rapport)
            relais = lots_de(siege.manage("echanges", "exporter", "--vers", "YDE", "--dossier", travail))[0]
            arrivee.manage("echanges", "importer", relais)
            arrivee.manage("echanges", "importer", relais)
            distant = arrivee.py(rapport)
        self.assertEqual(resultat_source["n_gl"], 2)  # apport et paiement ; le port dû n'est pas encore encaissé
        self.assertEqual((central["n_gl"], central["n_incidents"], central["resolu"]), (2, 1, True))
        self.assertEqual(Decimal(central["indemnite"]), Decimal("5000"))
        self.assertTrue(central["ecriture_liee"])
        self.assertEqual(central["trace"]["auteurs_ids"]["paye_par"], resultat_source["agent"])
        self.assertEqual((distant["n_gl"], distant["n_incidents"], distant["resolu"], distant["origine"]), (0, 1, True, "DLA"))
        self.assertFalse(distant["ecriture_liee"])
        self.assertEqual(distant["trace"]["ecriture"], resultat_source["ecriture"])
