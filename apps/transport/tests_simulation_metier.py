"""Flux fictifs réellement comptabilisés : colis, répartition de produits et simulation intégrée."""
import datetime
import io
import random
from decimal import Decimal
from types import SimpleNamespace
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from apps.comptabilite.models import Compte, Ecriture, Journal, LigneEcriture
from apps.comptabilite.services import creer_ecriture
from .models import Billet, Chauffeur, Colis, Depart, Gare, Ligne, Vehicule
from .models_incidents import Incident
from .models_suivi_colis import IncidentColis


class SuiviColisComptableTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_erp', verbosity=0)
        cls.admin=get_user_model().objects.create_superuser('suivi-test','','x')
        cls.lecture=get_user_model().objects.create_user('suivi-lecture','','x')
        cls.a=Gare.objects.create(code='SC-A',nom='Alpha',ville='Alpha')
        cls.b=Gare.objects.create(code='SC-B',nom='Beta',ville='Beta')
        cls.l=Ligne.objects.create(code='SC-AB',gare_depart=cls.a,gare_arrivee=cls.b,prix_billet=6000)
        cls.v=Vehicule.objects.create(immatriculation='COLIS-DEMO',nombre_places=30)
        cls.secours=Vehicule.objects.create(immatriculation='SECOURS-DEMO',nombre_places=30)
        cls.ch=Chauffeur.objects.create(nom='Chauffeur fictif')
        cls.ca=Journal.objects.get(code='CA')
        cls.compte=Compte.objects.get_or_create(numero='6580000',defaults={'intitule':'Indemnités fictives'})[0]
        capital=Compte.objects.get_or_create(numero='1010000',defaults={'intitule':'Capital fictif'})[0]
        creer_ecriture(cls.ca,datetime.date.today(),'Apport de test fictif',[
            {'compte':cls.ca.compte_tresorerie,'debit':1000000},{'compte':capital,'credit':1000000}])

    def setUp(self):
        self.client.force_login(self.admin)
        self.d=Depart.objects.create(ligne=self.l,vehicule=self.v,chauffeur=self.ch,
            date=datetime.date.today()-datetime.timedelta(days=1),heure=datetime.time(6))

    def colis(self, port=Colis.DU):
        c=Colis(gare_depart=self.a,gare_arrivee=self.b,expediteur='Expéditeur fictif',destinataire='Destinataire fictif',
            prix=2500,port=port,contre_remboursement=10000).enregistrer(self.admin)
        c.charger(self.d)
        return c

    def recette(self, vehicule):
        return sum((l.credit-l.debit for l in LigneEcriture.objects.filter(vehicule=vehicule,compte__numero__startswith='70612')),Decimal(0))

    def test_sans_trace_ne_declenche_ni_paiement_ni_livraison(self):
        c=self.colis();self.d.partir();self.d.arriver();c.refresh_from_db()
        n=Ecriture.objects.count()
        i=IncidentColis.declarer(c,IncidentColis.SANS_TRACE,'Alpha','Recherche fictive',self.admin)
        self.assertEqual(Ecriture.objects.count(),n)
        with self.assertRaisesMessage(ValidationError,'incident'):
            c.livrer(c.code_retrait,'Destinataire fictif',self.admin)
        self.assertEqual(Ecriture.objects.count(),n)
        self.assertIsNone(c.ecriture_livraison_id)
        self.assertIsNone(c.cr_reverse_le)
        self.assertEqual(IncidentColis.declarer(c,IncidentColis.SANS_TRACE,'Alpha','Recherche fictive',self.admin).pk,i.pk)

    def test_indemnisation_decision_puis_paiement_sans_doublon(self):
        c=self.colis();self.d.partir()
        i=IncidentColis.declarer(c,IncidentColis.PERDU,'Étape','Constat fictif',self.admin)
        n=Ecriture.objects.count()
        with self.assertRaises(ValidationError):
            i.payer(self.ca,self.admin)
        i.autoriser(10000,self.compte,self.admin)
        self.assertEqual(Ecriture.objects.count(),n)
        p=i.payer(self.ca,self.admin)
        i.payer(self.ca,self.admin)
        self.assertEqual(Ecriture.objects.count(),n+1)
        lignes=p.ecriture.lignes.all()
        self.assertEqual(sum(l.debit-l.credit for l in lignes),0)
        self.assertEqual(lignes.get(debit=10000).vehicule_id,self.v.pk)
        self.assertEqual(lignes.get(credit=10000).compte_id,self.ca.compte_tresorerie_id)
        with self.assertRaises(PermissionDenied):
            i.autoriser(10000,self.compte,self.lecture)
        with self.assertRaises(PermissionDenied):
            i.payer(self.ca,self.lecture)

    def test_colis_retrouve_encaissement_port_du_partage_apres_transvasement(self):
        c=self.colis();self.d.partir();Incident.transborder(self.d,40,self.secours);self.d.arriver();c.refresh_from_db()
        i=IncidentColis.declarer(c,IncidentColis.SANS_TRACE,'Beta','Recherche fictive',self.admin)
        n=Ecriture.objects.count();i.resoudre('Retrouvé, contrôle physique fictif',self.admin)
        self.assertEqual(Ecriture.objects.count(),n)
        c.livrer(c.code_retrait,'Destinataire fictif',self.admin)
        self.assertEqual((self.recette(self.v),self.recette(self.secours)),(1500,1000))
        self.assertEqual(c.ecriture_livraison.lignes.get(debit=12500).compte_id,self.ca.compte_tresorerie_id)
        c.reverser_contre_remboursement(self.admin)
        self.assertEqual(c.ecriture_reversement.lignes.get(credit=10000).compte_id,self.ca.compte_tresorerie_id)
        with self.assertRaises(ValidationError):
            c.reverser_contre_remboursement(self.admin)

    def test_port_paye_reparti_sans_nouvelle_recette_globale(self):
        self.colis(Colis.PAYE);self.d.partir()
        Incident.transborder(self.d,40,self.secours)
        self.assertEqual((self.recette(self.v),self.recette(self.secours)),(1500,1000))
        self.assertEqual(self.recette(self.v)+self.recette(self.secours),2500)

    def test_droits_et_fiche_montrent_l_incident(self):
        c=self.colis();IncidentColis.declarer(c,IncidentColis.ENDOMMAGE,'Alpha','Carton abîmé fictif',self.admin)
        url=reverse('transport:colis_detail',args=[c.pk])
        self.assertContains(self.client.get(url),'Carton abîmé fictif')
        self.client.force_login(self.lecture)
        i=IncidentColis.objects.get(colis=c)
        self.assertEqual(self.client.post(url,{'action':'autoriser_indemnite','incident':i.pk,'montant':'10000','compte':self.compte.pk}).status_code,403)
        self.assertEqual(self.client.post(url,{'action':'payer_indemnite','incident':i.pk,'caisse':self.ca.pk}).status_code,403)


class SimulationMetierIntegreeTests(TestCase):
    def test_scenarios_complets_et_rapprochements_gl_stock(self):
        from .management.commands.simulation import Command
        from apps.partenaires.models import ContratPartenaire
        c=Command()
        call_command(c,mois='2026-09',jours=1,vehicules=8,salaries=25,echelle=.05,
            scenarios_complets=True,departs_jour=4,forcer=True,stdout=io.StringIO())
        self.assertEqual(c.compteurs['voyages'],4)
        self.assertEqual(c.mesures[0]['departs'],4)
        self.assertTrue(c.mesures[0]['secondes']>0)
        self.assertTrue(all(ok for _,ok in c.controles),c.controles)
        self.assertEqual(IncidentColis.objects.count(),4)
        self.assertEqual(IncidentColis.objects.filter(resolu=False).count(),3)
        self.assertEqual(IncidentColis.objects.filter(ecriture__isnull=False).count(),2)
        self.assertTrue(any('Transvasement' in x['cas'] for x in c.scenarios))
        placement=next(x for x in c.scenarios if x['cas'].startswith('Placement'))
        self.assertEqual(placement['ecritures'],[])
        achat=next(x for x in c.scenarios if x['cas'].startswith('Achat de pièces pour le stock'))
        self.assertFalse(any(x['compte'].startswith('6') for x in achat['ecritures']))
        reparation=next(x for x in c.scenarios if x['cas'].startswith('Réparation :'))
        self.assertEqual(sum(Decimal(x['debit']) for x in reparation['ecritures'] if x['compte'].startswith('6')),5000)
        self.assertFalse(any(x['compte'].startswith('57') for x in reparation['ecritures']))
        for evenement in c.scenarios:
            self.assertEqual(Decimal(evenement['debit']),Decimal(evenement['credit']))
            for l in evenement['ecritures']:
                gl=LigneEcriture.objects.get(pk=l['source_gl_line_id'])
                self.assertEqual(gl.ecriture.statut,Ecriture.STATUT_VALIDEE)
                self.assertEqual(gl.debit,Decimal(l['debit']))
        self.assertEqual(c.hypotheses[0]['taux'],'15')
        self.assertEqual(set(c.hypotheses[0]['comparaison_sans_ecriture']),{ContratPartenaire.RECETTES,ContratPartenaire.MARGE})
        self.assertFalse(any(ct.montant_location for ct in c.contrats))


class PlanningExactTests(SimpleTestCase):
    def test_250_depart_pour_toutes_les_agences_sans_doublon_vehicule_heure(self):
        from .management.commands.simulation import Command
        c=Command();c.profil_complet=False;c.departs_jour=250;c.r=random.Random(2026)
        c.cars=[{'vehicule':SimpleNamespace(pk=i),'aller':'aller','retour':'retour'} for i in range(65)]
        plan=list(c.plan_journee(datetime.date(2026,9,1)))
        self.assertEqual(len(plan),250)
        self.assertEqual(len({(v['vehicule'].pk,h) for v,_,h in plan}),250)
        self.assertEqual({h for _,_,h in plan},{0,6,12,18})
