import datetime
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from apps.commercial.models import Tiers
from apps.comptabilite.models import Compte, Journal, Ecriture
from apps.comptabilite.services import creer_ecriture
from apps.transport.models import Vehicule
from .forms import ContratForm
from .models import ContratPartenaire, Decompte, DemandeRetrait, solde_partenaire


class AssietteEtRetraitsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_erp',verbosity=0)
        cls.p=Tiers.objects.create(code='P-DEMO',nom='Propriétaire fictif',type_tiers=Tiers.FOURNISSEUR)
        cls.v1=Vehicule.objects.create(immatriculation='PROP-DEMO-1',nombre_places=30)
        cls.v2=Vehicule.objects.create(immatriculation='PROP-DEMO-2',nombre_places=30)
        cls.jour=datetime.date.today();cls.ca=Journal.objects.get(code='CA')
        produit=Compte.objects.get_or_create(numero='7061100',defaults={'intitule':'Transport fictif'})[0]
        charge=Compte.objects.get_or_create(numero='6240000',defaults={'intitule':'Réparation fictive'})[0]
        for v in [cls.v1,cls.v2]:
            creer_ecriture(cls.ca,cls.jour,'Recettes de test',[
                {'compte':cls.ca.compte_tresorerie,'debit':1000000},{'compte':produit,'credit':1000000,'vehicule':v}])
            creer_ecriture(cls.ca,cls.jour,'Réparation de test',[
                {'compte':charge,'debit':200000,'vehicule':v},{'compte':cls.ca.compte_tresorerie,'credit':200000}])

    def contrat(self,v,base):
        return ContratPartenaire.objects.create(partenaire=self.p,vehicule=v,debut=self.jour,taux_commission=15,
                                                assiette_commission=base).activer()

    def test_comparaison_15_pourcent_recettes_ou_resultat(self):
        a=self.contrat(self.v1,ContratPartenaire.RECETTES)
        b=self.contrat(self.v2,ContratPartenaire.MARGE)
        x=Decompte.evaluer(a,self.jour,self.jour);y=Decompte.evaluer(b,self.jour,self.jour)
        self.assertEqual((x['commission'],x['montant_du']),(150000,650000))
        self.assertEqual((y['commission'],y['montant_du']),(120000,680000))
        self.assertEqual(ContratForm().initial['assiette_commission'],ContratPartenaire.A_CONFIRMER)

    def test_base_non_confirmee_ne_peut_etre_activee(self):
        c=ContratPartenaire.objects.create(partenaire=self.p,vehicule=self.v1,debut=self.jour,taux_commission=15,
                                          assiette_commission=ContratPartenaire.A_CONFIRMER)
        with self.assertRaisesMessage(ValidationError,'Confirmez'):
            c.activer()

    def test_deux_vehicules_un_compte_et_retrait_sans_nouvelle_charge(self):
        for v in [self.v1,self.v2]:
            Decompte.calculer(self.contrat(v,ContratPartenaire.RECETTES),self.jour,self.jour).approuver()
        self.assertEqual(solde_partenaire(self.p),1300000)
        retrait=DemandeRetrait(partenaire=self.p,date=self.jour,montant=100000).demander()
        retrait.decider(True)
        n=Ecriture.objects.count();copie=DemandeRetrait.objects.get(pk=retrait.pk)
        retrait.payer(self.ca)
        self.assertEqual(solde_partenaire(self.p),1200000)
        self.assertEqual(Ecriture.objects.count(),n+1)
        self.assertFalse(retrait.reglement.ecriture.lignes.filter(compte__numero__startswith='6').exists())
        with self.assertRaises(ValidationError):
            copie.payer(self.ca)
        self.assertEqual(Ecriture.objects.count(),n+1)
