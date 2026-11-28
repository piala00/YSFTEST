"""Recette P0 : validation et clôture sur instances périmées, pièces invalides et panne d'outbox.

Les montants et agences sont fictifs. Ces propriétés ne choisissent aucun schéma fiscal.
"""
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
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse

from apps.core import droits
from apps.core.models import Agence, DroitAcces, Exercice
from apps.echanges import publication
from apps.echanges.models import Evenement

from . import services
from .models import Compte, Ecriture, Journal, LigneEcriture


class ValidationP0Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_erp',verbosity=0)
        cls.exercice=Exercice.objects.first()
        cls.date=cls.exercice.date_debut+datetime.timedelta(days=10)
        Agence.objects.update(locale=False)
        Agence.objects.create(code='AUDIT',nom='Agence fictive audit',locale=True,uid=uuid.uuid4())
        cls.admin=get_user_model().objects.create_superuser('audit-p0','','Essai-fictif-2026')
        cls.groupe=Group.objects.create(name='Audit consultation')
        cls.lecteur=get_user_model().objects.create_user('lecture-p0',password='Essai-fictif-2026')
        cls.lecteur.groups.add(cls.groupe)
        DroitAcces.objects.create(groupe=cls.groupe,module='comptabilite',code='traitement',niveau=droits.LECTURE)

    def brouillard(self,lignes=None,date=None):
        e=Ecriture.objects.create(journal=Journal.objects.get(code='OD'),exercice=self.exercice,
            numero=f'AUDIT-{Ecriture.objects.count()+1}',date=date or self.date,libelle='Pièce fictive P0')
        for compte,debit,credit in lignes or [('5711',1000,0),('101',0,1000)]:
            LigneEcriture.objects.create(ecriture=e,compte=Compte.objects.get(numero=compte),debit=debit,credit=credit)
        return e

    def evenements(self,e):
        return Evenement.objects.filter(type='ecriture',objet_uid=e.uid)

    def test_ecriture_hors_bornes_de_son_exercice_refusee(self):
        e=self.brouillard(date=self.exercice.date_fin+datetime.timedelta(days=1))
        with self.assertRaises(ValidationError):
            e.valider()
        e.refresh_from_db();self.assertEqual(e.statut,Ecriture.STATUT_BROUILLARD)
        self.assertFalse(self.evenements(e).exists())

    def test_lignes_invalides_refusees_meme_si_les_totaux_sont_equilibres(self):
        cas=[ [('5711',1000,0),('5711',-100,0),('101',0,900)],
              [('5711',1000,1000)],
              [('5711',1000,0),('101',0,1000),('101',0,0)] ]
        for lignes in cas:
            with self.subTest(lignes=lignes):
                e=self.brouillard(lignes=lignes)
                with self.assertRaises(ValidationError):
                    e.valider()
                e.refresh_from_db();self.assertEqual(e.statut,Ecriture.STATUT_BROUILLARD)
                self.assertFalse(self.evenements(e).exists())

    def test_exercice_cloture_apres_chargement_est_refuse(self):
        e=self.brouillard()
        Exercice.objects.filter(pk=self.exercice.pk).update(cloture=True)
        with self.assertRaises(ValidationError):
            e.valider()
        e.refresh_from_db();self.assertEqual(e.statut,Ecriture.STATUT_BROUILLARD)

    def test_journal_cloture_apres_chargement_est_refuse(self):
        e=self.brouillard()
        Journal.objects.filter(pk=e.journal_id).update(cloture_au=self.date)
        with self.assertRaises(ValidationError):
            e.valider()
        e.refresh_from_db();self.assertEqual(e.statut,Ecriture.STATUT_BROUILLARD)

    def test_double_validation_depuis_instance_perimee_publie_une_seule_fois(self):
        e=self.brouillard();autre=Ecriture.objects.get(pk=e.pk)
        e.valider();autre.valider()
        self.assertEqual(self.evenements(e).count(),1)
        self.assertEqual(self.evenements(e).get().revision,1)

    def test_panne_publication_annule_validation_et_evenement(self):
        e=self.brouillard();publier=publication.publier_ecriture
        def panne(piece):
            publier(piece)
            raise RuntimeError('Incident fictif après écriture outbox')
        with mock.patch.object(publication,'publier_ecriture',side_effect=panne):
            with self.assertRaises(RuntimeError):
                e.valider()
        e.refresh_from_db();self.assertEqual(e.statut,Ecriture.STATUT_BROUILLARD)
        self.assertFalse(self.evenements(e).exists())
        e.valider()
        self.assertEqual(self.evenements(e).count(),1)

    def test_validation_equilibree_publie_les_lignes_validees(self):
        e=self.brouillard();e.valider();e.refresh_from_db()
        self.assertEqual(e.statut,Ecriture.STATUT_VALIDEE)
        self.assertEqual(e.total_debit,e.total_credit)
        self.assertEqual(self.evenements(e).count(),1)

    def test_GET_ne_valide_et_ne_supprime_pas(self):
        self.client.force_login(self.admin)
        e=self.brouillard()
        for nom in ('ecriture_valider','ecriture_supprimer'):
            with self.subTest(action=nom):
                r=self.client.get(reverse('comptabilite:'+nom,args=[e.pk]))
                self.assertEqual(r.status_code,405)
                e.refresh_from_db();self.assertEqual(e.statut,Ecriture.STATUT_BROUILLARD)
        self.assertFalse(self.evenements(e).exists())

    def test_profil_lecture_refuse_les_actions_POST(self):
        self.client.force_login(self.lecteur)
        for nom in ('ecriture_valider','ecriture_supprimer'):
            with self.subTest(action=nom):
                e=self.brouillard()
                r=self.client.post(reverse('comptabilite:'+nom,args=[e.pk]))
                actuel=Ecriture.objects.filter(pk=e.pk)
                self.assertEqual((r.status_code,actuel.exists(),actuel.values_list('statut',flat=True).first()),
                                 (403,True,Ecriture.STATUT_BROUILLARD))
                self.assertFalse(self.evenements(e).exists())

    def test_ecriture_validee_non_supprimable_par_HTTP(self):
        self.client.force_login(self.admin)
        e=self.brouillard();e.valider()
        self.client.post(reverse('comptabilite:ecriture_supprimer',args=[e.pk]))
        e.refresh_from_db();self.assertEqual(e.statut,Ecriture.STATUT_VALIDEE)
        self.assertEqual(self.evenements(e).count(),1)

    def test_double_cloture_depuis_instance_perimee_ne_double_pas_les_reports(self):
        e=self.brouillard();e.valider()
        ancienne=Exercice.objects.get(pk=self.exercice.pk)
        services.cloturer_exercice(self.exercice)
        n=Ecriture.objects.filter(origine=f'Clôture {self.exercice.code}').count()
        with self.assertRaises(ValidationError):
            services.cloturer_exercice(ancienne)
        self.assertEqual(Ecriture.objects.filter(origine=f'Clôture {self.exercice.code}').count(),n)


@skipUnlessDBFeature('has_select_for_update')
class ValidationConcurrenteP0Tests(TransactionTestCase):
    """Vrais accès concurrents sur un moteur à verrou de ligne ; exécutés notamment en CI SQL Server."""
    def setUp(self):
        call_command('init_erp',verbosity=0)
        self.exercice=Exercice.objects.first()
        self.date=self.exercice.date_debut+datetime.timedelta(days=10)
        Agence.objects.update(locale=False)
        Agence.objects.create(code='AUDIT',nom='Agence fictive concurrence',locale=True,uid=uuid.uuid4())
        self.ecriture=services.creer_ecriture(Journal.objects.get(code='OD'),self.date,'Essai concurrent fictif',
            [{'compte':Compte.objects.get(numero='5711'),'debit':1000},
             {'compte':Compte.objects.get(numero='101'),'credit':1000}],valider=False)

    def executer_deux(self,charger,action):
        barriere=Barrier(2,timeout=20)
        def travail():
            close_old_connections()
            try:
                connexion=connections['default']
                with connexion.cursor() as curseur:
                    if connexion.vendor in ('microsoft','mssql'):
                        curseur.execute('SET LOCK_TIMEOUT 15000')
                    elif connexion.vendor=='postgresql':
                        curseur.execute("SET lock_timeout = '15s'")
                instance=charger()
                barriere.wait()
                try:
                    action(instance)
                    return 'ok'
                except ValidationError:
                    return 'refus'
            finally:
                connections['default'].close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(travail) for _ in range(2)]
            return [f.result(timeout=45) for f in futures]

    def test_deux_validations_concurrentes_une_seule_publication(self):
        resultat=self.executer_deux(lambda:Ecriture.objects.get(pk=self.ecriture.pk),lambda e:e.valider())
        self.assertEqual(resultat,['ok','ok'])
        self.ecriture.refresh_from_db()
        self.assertEqual(self.ecriture.statut,Ecriture.STATUT_VALIDEE)
        self.assertEqual(Evenement.objects.filter(type='ecriture',objet_uid=self.ecriture.uid).count(),1)

    def test_deux_clotures_concurrentes_un_seul_report(self):
        self.ecriture.valider()
        resultat=self.executer_deux(lambda:Exercice.objects.get(pk=self.exercice.pk),services.cloturer_exercice)
        self.assertEqual(sorted(resultat),['ok','refus'])
        self.assertEqual(Ecriture.objects.filter(origine=f'Clôture {self.exercice.code}').count(),1)
