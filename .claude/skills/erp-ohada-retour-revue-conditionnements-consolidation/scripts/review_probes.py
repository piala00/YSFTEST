import datetime
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.authtoken.models import Token
from apps.commercial import tests_fiche_stock as fs, fiche_stock
from apps.reporting import tests_rapport_commercial as rs, services
from apps.commercial.models import PointageFiche, Document, Reglement, StockDepot
from apps.core.models import DroitAcces

class StockReview(TestCase):
    piece=fs.FicheStockTests.__dict__['piece']
    @classmethod
    def setUpTestData(cls):
        fs.FicheStockTests.setUpTestData.__func__(cls)

    def test_R17_blank_is_not_zero(self):
        self.client.force_login(self.fichiste)
        r=self.client.post(reverse('commercial:pointage'),{'numero':self.livraison.numero,'depot':self.depot.pk})
        count=PointageFiche.objects.filter(document=self.livraison).count()
        print('PROBE R17',{'http':r.status_code,'pointages_after_blank':count},flush=True)
        self.assertEqual(count,0,'Une quantité absente ne doit pas produire un pointage validé.')

    def test_R14_restricted_api_list(self):
        group=Group.objects.create(name='Fichiste controle')
        self.fichiste.groups.add(group)
        for root in ['fichier','edition','structure','traitement','etat']:
            DroitAcces.objects.create(groupe=group,module='commercial',code=root,niveau='INTERDIT')
        DroitAcces.objects.create(groupe=group,module='commercial',code='fiche_stock.pointage',niveau='TOUT')
        self.client.force_login(self.fichiste)
        specific=self.client.get('/api/documents/?type=LIVRAISON')
        broad=self.client.get('/api/documents/')
        body=broad.json() if broad.status_code==200 else {}
        data=body.get('results',[]) if isinstance(body,dict) else body
        expected_exposed=any(x.get('id')==self.livraison.pk and x.get('lignes',[{}])[0].get('quantite')==10 for x in data)
        print('PROBE R14',{'filtered_http':specific.status_code,'broad_http':broad.status_code,'expected_quantity_exposed':expected_exposed},flush=True)
        self.assertFalse(expected_exposed,'L’API sans filtre ne doit pas révéler les quantités interdites.')

    def test_R19_original_fichiste_preserved(self):
        p=PointageFiche(document=self.livraison,depot=self.depot,fichiste=self.fichiste,cree_par=self.fichiste).enregistrer({self.huile.pk:Decimal('12')})
        second=get_user_model().objects.create_user('second-fichiste','','x')
        self.client.force_login(second)
        self.client.post(reverse('commercial:pointage'),{'numero':self.livraison.numero,'depot':self.depot.pk,f'qte_{self.huile.pk}':'10','observation':'Correction de lecture'})
        p.refresh_from_db()
        print('PROBE HISTORIQUE',{'createur':p.cree_par.username,'ancien_fichiste_historique':p.historique[0]['fichiste'],'correcteur':second.username},flush=True)
        self.assertEqual(p.historique[0]['fichiste'],self.fichiste.username,'L’historique doit garder l’auteur de la déclaration remplacée.')

    def test_R18_missing_pointage_not_complete_stock(self):
        PointageFiche(document=self.entree,depot=self.depot).enregistrer({self.huile.pk:Decimal('100')})
        f=fiche_stock.fiche_article(self.huile,self.depot,self.jour,self.jour)
        pending=[l for l in f['lignes'] if not l['pointe']]
        print('PROBE FICHE',{'fiche_balance':str(f['solde_fiche']),'machine_balance':str(f['solde_machine']),'pending_rows':len(pending),'pending_outgoing':str(pending[0]['sortie'])},flush=True)
        self.assertNotEqual(f['solde_fiche'],f['solde_machine'],'Une sortie non déclarée ne doit pas être reprise automatiquement dans un registre indépendant.')

    def test_R17_negative_quantity_rejected(self):
        self.client.force_login(self.fichiste)
        r=self.client.post(reverse('commercial:pointage'),{'numero':self.livraison.numero,'depot':self.depot.pk,f'qte_{self.huile.pk}':'-5'})
        p=PointageFiche.objects.filter(document=self.livraison).first()
        print('PROBE NEGATIVE',{'http':r.status_code,'saved':bool(p),'quantity':str(p.lignes.first().quantite_saisie) if p else None},flush=True)
        self.assertIsNone(p,'La sortie déclarée est une quantité absolue ; une valeur négative doit être rejetée.')

    def test_R13_partial_delivery_then_invoice(self):
        order=self.piece(Document.COMMANDE,10,self.client_)
        delivery=order.transformer(Document.LIVRAISON)
        line=delivery.lignes.get();line.quantite=4;line.save();delivery.recalculer();delivery.valider()
        invoice=delivery.transformer(Document.FACTURE);invoice.valider()
        order.refresh_from_db()
        pending=order.lignes.get().reste_a_transformer
        stock=StockDepot.quantite_de(self.huile.pk,self.depot.pk)
        print('PROBE PARTIEL',{'ordered':10,'delivered':str(line.quantite),'remaining':str(pending),'invoice_quantity':str(invoice.lignes.get().quantite),'stock':str(stock)},flush=True)
        self.assertEqual(pending,Decimal('6'))
        self.assertEqual(invoice.lignes.get().quantite,Decimal('4'))
        self.assertEqual(stock,Decimal('86'))

class ReportReview(TestCase):
    piece=rs.RapportCommercialTests.piece
    regler=rs.RapportCommercialTests.regler
    @classmethod
    def setUpTestData(cls):rs.RapportCommercialTests.setUpTestData.__func__(cls)

    def test_R26_old_report_does_not_change_with_future_payment(self):
        yesterday=self.jour-datetime.timedelta(days=1)
        doc=self.piece(Document.FACTURE,3,valider=False)
        doc.date=yesterday;doc.save();doc.valider()
        before=services.rapport_commercial(yesterday)['ventes']['credit']
        self.regler(3000,facture=doc,date=self.jour)
        after=services.rapport_commercial(yesterday)['ventes']['credit']
        print('PROBE RAPPORT PASSE',{'credit_initial':str(before),'credit_apres_paiement_futur':str(after)},flush=True)
        self.assertEqual(after,before,'Un rapport de la veille doit calculer le reste dû à sa date, pas le solde courant.')

    def test_R09_mobile_money_must_not_increase_cash(self):
        doc=self.piece(Document.FACTURE,3)
        modes=dict(Reglement.MODES)
        mode=next((k for k,v in modes.items() if 'mobile' in v.lower()),None)
        if mode is None:self.skipTest('Mode mobile absent')
        before=services.rapport_commercial(self.jour)['solde']['cloture']
        self.regler(3000,facture=doc,mode=mode)
        after=services.rapport_commercial(self.jour)['solde']['cloture']
        print('PROBE MOBILE',{'mode':mode,'cash_before':str(before),'cash_after':str(after)},flush=True)
        self.assertEqual(before,after,'Un mode Mobile Money ne doit pas alimenter une caisse espèces sans règle explicite.')
