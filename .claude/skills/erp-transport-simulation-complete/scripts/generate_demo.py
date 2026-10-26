#!/usr/bin/env python3
"""Jeu de démonstration reproductible ERP Transport Afrique Centrale; Python stdlib.
N'est PAS un moteur comptable réglementaire. Les comptes sont des symboles DEMO à paramétrer.
"""
import csv, random, calendar, collections, json, hashlib, sys
from pathlib import Path
from datetime import date, timedelta

SEED=20260926
random.seed(SEED)
BASE=Path(__file__).resolve().parent.parent/'examples'/'demo_2026_09'
BASE.mkdir(parents=True,exist_ok=True)
rows=collections.defaultdict(list)
seq=collections.Counter()
bal=collections.defaultdict(int)
trip_revenue=collections.defaultdict(int)
trip_direct=collections.defaultdict(int)
vehicle_products=collections.defaultdict(int)
vehicle_costs=collections.defaultdict(int)
partner_due=collections.defaultdict(int)
agencies=[('AG01','Douala',65,12),('AG02','Yaoundé',64,12),('AG03','Bafoussam',34,8),('AG04','Bertoua',32,8),('AG05','Garoua-Boulaï',26,5),('AG06','Ngaoundéré',30,6),('AG07','Bamenda',27,5),('AG08','Buea',22,4)]
assert sum(a[2] for a in agencies)==300 and sum(a[3] for a in agencies)==60
for i,(aid,city,staff,cap) in enumerate(agencies):
    rows['agences'].append(dict(agency_id=aid,ville=city,employes_attendus=staff,vehicules_voyageurs_attendus=cap,mode_caisses='MULTI' if i<3 else 'UNIQUE',siege='OUI' if i==0 else 'NON'))
    for c in (['BILLET','COURRIER','GARAGE','CENTRALE'] if i<3 else ['CAISSE_UNIQUE']):
        rows['caisses'].append(dict(caisse_id=f'{aid}-{c}',agency_id=aid,service=('TOUS' if c=='CAISSE_UNIQUE' else c),mode='ESPECES'))

# 60 bus + 5 messagerie, sièges et gammes fixés, datation propriétaire.
fleet_specs=[('VIP',15)]*12+[('VIP',20)]*8+[('VIP',30)]*4+[('CLASSIQUE',30)]*6+[('CLASSIQUE',40)]*10+[('CLASSIQUE',55)]*12+[('CLASSIQUE',75)]*8
random.shuffle(fleet_specs)
agency_for_bus=[]
for ag in agencies: agency_for_bus.extend([ag[0]]*ag[3])
random.shuffle(agency_for_bus)
partner_idx=set(random.sample(range(60),15))
partner_list=[f'PAR-{i:03d}' for i in range(1,11)]
for p in partner_list: rows['partenaires'].append(dict(partner_id=p,nom_fictif=f'Partenaire privé {p[-3:]}',type='PERSONNE_PHYSIQUE_FICTIVE'))
partners_assign={j: partner_list[i%10] for i,j in enumerate(sorted(partner_idx))}
vehicle_ag={}
vehicle_owner={}
vehicle_range={}
vehicle_seats={}
for j,((gamme,places),ag) in enumerate(zip(fleet_specs,agency_for_bus),1):
    vid=f'BUS-{j:03d}'; partner=partners_assign.get(j-1,'COMPAGNIE'); vehicle_ag[vid]=ag;vehicle_owner[vid]=partner;vehicle_range[vid]=gamme;vehicle_seats[vid]=places
    typ=('MINIBUS' if places<=20 else 'COASTER' if places<=30 else 'BUS' if places<=55 else 'GRAND_AUTOCAR_TYPE_SAVIEM')
    rows['vehicules'].append(dict(vehicule_id=vid,immatriculation_fictive=f'DEMO-{j:03d}-CM',agence_attache=ag,gamme=gamme,type=typ,places=places,proprietaire=partner,transport='VOYAGEURS',date_debut_affectation='2026-09-01'))
    if partner!='COMPAGNIE':
        rows['contrats'].append(dict(contrat_id=f'CTR-{vid}',vehicule_id=vid,partenaire_id=partner,debut='2026-09-01',fin='',mode='REDEVANCE_VARIABLE',assiette='70% du résultat contributif de véhicule avant redevance, avec exclusions documentées',taux_simule='0.70',conditions='FICTIF - à formaliser et faire valider'))
for k,ag in enumerate(['AG01','AG01','AG02','AG03','AG04'],1):
    vid=f'FRET-{k:03d}';vehicle_ag[vid]=ag;vehicle_owner[vid]='COMPAGNIE';vehicle_range[vid]='COURRIER';vehicle_seats[vid]=0
    rows['vehicules'].append(dict(vehicule_id=vid,immatriculation_fictive=f'DEMO-F-{k:03d}',agence_attache=ag,gamme='COURRIER',type='UTILITAIRE_CAISSE',places=0,proprietaire='COMPAGNIE',transport='COURRIER',date_debut_affectation='2026-09-01'))

# 120 agents équipage rattachés aux véhicules, 180 collaborateurs par agence.
counts=collections.Counter(); staffid=0
salaries={}
for vid in [v for v in vehicle_ag if v.startswith('BUS')]:
    ag=vehicle_ag[vid]
    for fonction in ['CHAUFFEUR','CONVOYEUR']:
        staffid+=1; emp=f'EMP-{staffid:04d}'; brut=random.choice([115000,130000,145000,165000,185000]) if fonction=='CHAUFFEUR' else random.choice([90000,105000,120000])
        rows['employes'].append(dict(employe_id=emp,nom_fictif=f'Employé de démonstration {staffid:04d}',agence=ag,fonction=fonction,vehicule_rattache=vid,salaire_brut_mensuel_simule=brut))
        counts[ag]+=1;salaries[emp]=brut
others=['BILLETTERIE','COURRIER','GARAGE','COMPTABILITE_CAISSE','DIRECTION','ADMINISTRATION','RH_PAIE','ACHATS_STOCKS','SECURITE','TECHNIQUE']
for ag,city,quota,_ in agencies:
    for _ in range(quota-counts[ag]):
        staffid+=1;emp=f'EMP-{staffid:04d}';func=random.choices(others,weights=[19,15,12,12,4,10,5,8,8,7])[0];brut=random.choice([85000,95000,110000,125000,150000,175000,210000,240000])
        rows['employes'].append(dict(employe_id=emp,nom_fictif=f'Employé de démonstration {staffid:04d}',agence=ag,fonction=func,vehicule_rattache='',salaire_brut_mensuel_simule=brut));counts[ag]+=1;salaries[emp]=brut
assert len(rows['employes'])==300 and all(counts[a[0]]==a[2] for a in agencies)

# Comptabilité GA seule source. Analytique produite uniquement pour comptes produits/charges APRES écriture GA validée.
accounts={
'101-DEMO':'Capital de simulation - ouverture',
'521-DEMO':'Banque de simulation',
'552-DEMO':'Monnaie électronique mobile',
'5711-DEMO':'Caisse de simulation',
'401-DEMO':'Fournisseurs',
'31-DEMO':'Stocks de pièces et consommables (compte à paramétrer)',
'2-DEMO':'Immobilisations et matériels (compte à paramétrer)',
'422-DEMO':'Personnel net à payer',
'431-DEMO':'Organismes sociaux - démonstration',
'467-DEMO':'Partenaires - redevances à payer',
'706-V':'Prestations de voyageurs',
'706-C':'Prestations de messagerie',
'605-F':'Carburant consommé',
'63-PE':'Péages et frais de route (imputation à valider)',
'624-R':'Entretien et réparation',
'60-S':'Consommation pièces et fournitures (imputation à valider)',
'661-DEMO':'Rémunérations brutes - simulation',
'664-DEMO':'Charges sociales employeur - simulation',
'63-PART':'Redevances partenaires - simulation (qualification à valider)',
}
for c,n in accounts.items():rows['comptes_demo'].append(dict(code_demo=c,intitule=n,note='Les subdivisions -DEMO ne sont pas des numéros réglementaires définitifs. Faire valider les comptes OHADA.'))
REV={'706-V','706-C'}
CHARGES={'605-F','63-PE','624-R','60-S','661-DEMO','664-DEMO','63-PART'}

def entry(day,journal,ref,legs,source_type,source_id,ag='',veh='',service=''):
    assert sum(d-c for code,d,c in legs)==0,(ref,legs)
    eid=f'EC-{len(rows["ecritures_entetes"])+1:07d}'
    rows['ecritures_entetes'].append(dict(ecriture_id=eid,date=day,journal=journal,reference=ref,source_type=source_type,source_id=source_id,agence=ag,statut='COMPTABILISE',debit=sum(d for _,d,c in legs),credit=sum(c for _,d,c in legs)))
    for code,d,c in legs:
        seq['ligne']+=1; line=f'LG-{seq["ligne"]:08d}'
        rows['ecritures_lignes'].append(dict(ligne_id=line,ecriture_id=eid,date=day,compte=code,intitule=accounts[code],debit=d,credit=c,agence=ag,document=ref,source_type=source_type,source_id=source_id,statut='COMPTABILISE'))
        bal[code]+=d-c
        if code in REV or code in CHARGES:
            amount=c-d  # produits crédités positifs, charges débitées négatives
            rows['ventilations_analytiques'].append(dict(ventilation_id=f'AN-{len(rows["ventilations_analytiques"])+1:08d}',source_gl_line_id=line,source_gl_entry_id=eid,vehicule=veh or 'NON_AFFECTE',proprietaire=vehicle_owner.get(veh,'NON_AFFECTE'),agence=ag,service=service,compte=code,montant_signe_resultat=amount,statut='SOURCE_COMPTABILISEE'))
            if veh:
                if amount>=0: vehicle_products[veh]+=amount
                else: vehicle_costs[veh]+=-amount
    return eid

# Apports réels simulés (solde début de mois) : banque au siège, caisses de chaque agence.
entry('2026-09-01','OUVERTURE','APPORT-2026-09', [('521-DEMO',200000000,0),('101-DEMO',0,200000000)],'OUVERTURE','CAPITAL-INITIAL','AG01')
for ag,_,_,_ in agencies:
    entry('2026-09-01','OUVERTURE',f'CAISSE-INIT-{ag}', [('5711-DEMO',2000000,0),('101-DEMO',0,2000000)],'OUVERTURE',f'CAISSE-INIT-{ag}',ag)

routes={ag[0]:[b[0] for b in agencies if b[0]!=ag[0]] for ag in agencies}
citymap={a[0]:a[1] for a in agencies}

def prix(gam,places):
    base=random.choice([5000,6000,7000,8000,9000])
    return base+(random.choice([3500,5000,6500,8000]) if gam=='VIP' else 0)

def daystr(d):return f'2026-09-{d:02d}'

# Voyages + tickets individuellement identifiés. Un batch comptable par départ/mode paiement.
for d in range(1,31):
  for vid in [v for v in vehicle_ag if v.startswith('BUS')]:
    if random.random()>0.70:continue
    ag=vehicle_ag[vid];gam=vehicle_range[vid];capacity=vehicle_seats[vid]
    dest=random.choice(routes[ag]);p=prix(gam,capacity);occup=random.uniform(0.52,0.94)
    n=max(1,min(capacity,round(capacity*occup)))
    tid=f'VOY-{d:02d}-{vid}'
    rows['voyages'].append(dict(voyage_id=tid,date_depart=daystr(d),agence_exploitation=ag,vehicule_id=vid,gamme=gam,origine=citymap[ag],destination=citymap[dest],capacite=capacity,voyageurs=n,prix_unitaire=p,statut='EFFECTUE_SIMULE'))
    trip_revenue[tid]=n*p
    all_meth=collections.defaultdict(list)
    for seat in range(1,n+1):
        vend_ag=ag if random.random()<0.88 else random.choice([x[0] for x in agencies if x[0]!=ag])
        mode='ESPECES' if random.random()<0.72 else 'MOBILE'
        batch=f'VTE-{tid}-{vend_ag}-{mode}'
        ticket=f'BIL-{tid}-{seat:03d}'
        rows['billets'].append(dict(billet_id=ticket,voyage_id=tid,vehicule_id=vid,agence_vente=vend_ag,agence_exploitation=ag,place=seat,date_vente=daystr(d),date_depart=daystr(d),gamme=gam,tarif=p,moyen_paiement=mode,lot_comptable=batch,statut='EMBARQUE_SIMULE',validation_code=f'HASH-{hashlib.sha256(ticket.encode()).hexdigest()[:16]}'))
        all_meth[(vend_ag,mode,batch)].append(ticket)
    for (sellag,mode,batch), tickets in all_meth.items():
        amount=len(tickets)*p
        cash='5711-DEMO' if mode=='ESPECES' else '552-DEMO'
        entry(daystr(d),'VENTES',batch,[(cash,amount,0),('706-V',0,amount)],'LOT_BILLETS',batch,sellag,vid,'BILLETTERIE')
    # frais route payés en espèces dans agence d'exploitation
    fuel=random.randrange(25000,80001,5000) if capacity<=40 else random.randrange(45000,120001,5000)
    toll=random.randrange(2000,12001,1000)
    expid=f'DEP-{tid}-CARB'
    rows['depenses'].append(dict(depense_id=expid,date=daystr(d),agence=ag,vehicule=vid,voyage=tid,nature='CARBURANT',montant=fuel,moyen_paiement='ESPECES',document_source=expid))
    entry(daystr(d),'CAISSE',expid,[('605-F',fuel,0),('5711-DEMO',0,fuel)],'DEPENSE_CARBURANT',expid,ag,vid,'EXPLOITATION')
    expid=f'DEP-{tid}-PEAGE'
    rows['depenses'].append(dict(depense_id=expid,date=daystr(d),agence=ag,vehicule=vid,voyage=tid,nature='PEAGES',montant=toll,moyen_paiement='ESPECES',document_source=expid))
    entry(daystr(d),'CAISSE',expid,[('63-PE',toll,0),('5711-DEMO',0,toll)],'DEPENSE_PEAGE',expid,ag,vid,'EXPLOITATION')
    trip_direct[tid]=fuel+toll

# Messagerie: 7 à 14 expéditions/jour/agence, livrées dans la journée dans ce jeu simplifié
for d in range(1,31):
  for ag,city,_,_ in agencies:
    eligible=[v for v in vehicle_ag if vehicle_ag[v]==ag]
    for _ in range(random.randint(7,14)):
        seq['colis']+=1;num=f'COL-202609-{seq["colis"]:06d}'
        dest=random.choice(routes[ag]);veh=random.choice(eligible)
        amount=random.choice([2500,3000,4000,5000,7500,10000,15000]);mode='ESPECES' if random.random()<0.75 else 'MOBILE'
        rows['colis'].append(dict(bordereau=num,date_acceptation=daystr(d),date_livraison=daystr(d),agence_depart=ag,destination=citymap[dest],designation=random.choice(['Carton','Documents','Sac','Pièces détachées']),vehicule_transporteur=veh,mode=mode,montant=amount,statut='LIVRE_SIMULE',hypothese='Prestation achevée le jour même dans ce jeu de démonstration'))
        entry(daystr(d),'VENTES',num,[('5711-DEMO' if mode=='ESPECES' else '552-DEMO',amount,0),('706-C',0,amount)],'COLIS_LIVRE',num,ag,veh,'COURRIER')

# Achats: pièces, ruban adhésif, fournitures, et matériel immobilisé; circuits complets.
items=[('PIECE-FILTRE','PIECE_GARAGE',40000,'STOCK'),('RUBAN-ADH','EMBALLAGE',1200,'STOCK'),('CARTON-M','EMBALLAGE',1800,'STOCK'),('PAPIER-A4','BUREAU',3500,'STOCK'),('IMPR-THERM','MATERIEL',250000,'IMMOBILISATION')]
for sku,cat,unit,nature in items:rows['articles'].append(dict(article_id=sku,designation=cat,prix_fictif_unitaire=unit,nature=nature))
stock=collections.Counter()
for d in [3,10,17,24]:
  for idx,(ag,city,_,_) in enumerate(agencies):
    acheteur='AG01' if ((d+idx)%3==0) else ag
    req=f'DA-{ag}-{d:02d}'; quote=f'DEV-{ag}-{d:02d}'; po=f'BC-{ag}-{d:02d}';gr=f'BR-{ag}-{d:02d}'; invoice=f'FAC-{ag}-{d:02d}'
    supplier=f'FOUR-{(idx+d)%6+1:02d}'
    rows['demandes_achat'].append(dict(da_id=req,date=daystr(d),agence_beneficiaire=ag,service='GARAGE_COURRIER_BUREAU',statut='APPROUVEE_SIMULEE'))
    rows['devis_fournisseurs'].append(dict(devis_id=quote,da_id=req,fournisseur=supplier,date=daystr(d),statut='RETENU_SIMULE',simulation='Oui'))
    rows['bons_commande'].append(dict(bc_id=po,devis_id=quote,date=daystr(d),agence_acheteuse=acheteur,agence_destinataire=ag,fournisseur=supplier,statut='RECEPTIONNE_SIMULE'))
    rows['receptions'].append(dict(reception_id=gr,bc_id=po,date=daystr(d),depot=f'{ag}-DEPOT',statut='CONFORME_SIMULE'))
    lines=[('PIECE-FILTRE',random.randint(4,8)),('RUBAN-ADH',random.randint(40,80)),('CARTON-M',random.randint(30,60)),('PAPIER-A4',random.randint(12,28))]
    if d==3 and idx<3:lines.append(('IMPR-THERM',1))
    total=0;st=0;assets=0
    itemmap={item[0]:item for item in items}
    for sku,qty in lines:
       cat=itemmap[sku][1];unit=itemmap[sku][2];nature=itemmap[sku][3]
       amount=qty*unit;total+=amount
       if nature=='STOCK':stock[(ag,sku)]+=qty;st+=amount
       else:assets+=amount
       rows['lignes_achats'].append(dict(bc_id=po,article_id=sku,quantite=qty,prix_unitaire=unit,total=amount,nature=nature))
       rows['mouvements_stock'].append(dict(mouvement_id=f'STK-{len(rows["mouvements_stock"])+1:06d}',date=daystr(d),type='RECEPTION' if nature=='STOCK' else 'EQUIPEMENT_IMMOBILISE',article_id=sku,agence=ag,depot=f'{ag}-DEPOT',quantite_entree=qty,quantite_sortie=0,vehicule='',document=gr))
    rows['factures_fournisseurs'].append(dict(facture_id=invoice,bc_id=po,reception_id=gr,date=daystr(d),fournisseur=supplier,agence_beneficiaire=ag,montant_ht_demo=total,statut='COMPTABILISEE_SIMULEE',verification='3-WAY-MATCH-OK'))
    legs=[]
    if st:legs.append(('31-DEMO',st,0))
    if assets:legs.append(('2-DEMO',assets,0))
    legs.append(('401-DEMO',0,total))
    entry(daystr(d),'ACHATS',invoice,legs,'FACTURE_ACHAT',invoice,ag,'','ACHATS')
    # Paiement fournisseur partiel au jour 28; reliquat demeure dû
    payamt=round(total*.75)
    rows['reglements_fournisseurs'].append(dict(paiement_id=f'REG-{invoice}',facture_id=invoice,date='2026-09-28',montant=payamt,moyen='BANQUE',statut='PAYE_SIMULE'))
    entry('2026-09-28','BANQUE',f'REG-{invoice}',[('401-DEMO',payamt,0),('521-DEMO',0,payamt)],'REGLEMENT_FOURNISSEUR',f'REG-{invoice}',ag)

# Consommations de stock après chaque réception, imputées (si garage) au véhicule réellement affecté.
for d in range(4,31):
 for ag,*_ in agencies:
    avail=[v for v in vehicle_ag if vehicle_ag[v]==ag and v.startswith('BUS')]
    for sku,q,service in [('RUBAN-ADH',2,'COURRIER'),('CARTON-M',1,'COURRIER'),('PAPIER-A4',1,'ADMINISTRATION')]:
        if stock[(ag,sku)]>=q:
            stock[(ag,sku)]-=q;seq['issue']+=1; ref=f'SOR-{seq["issue"]:06d}';unit={x[0]:x[2] for x in items}[sku];amount=q*unit
            rows['consommations_stock'].append(dict(sortie_id=ref,date=daystr(d),agence=ag,article=sku,quantite=q,cout=amount,vehicule='',service=service))
            rows['mouvements_stock'].append(dict(mouvement_id=f'STK-{len(rows["mouvements_stock"])+1:06d}',date=daystr(d),type='CONSOMMATION',article_id=sku,agence=ag,depot=f'{ag}-DEPOT',quantite_entree=0,quantite_sortie=q,vehicule='',document=ref))
            entry(daystr(d),'STOCK',ref,[('60-S',amount,0),('31-DEMO',0,amount)],'CONSOMMATION_STOCK',ref,ag,'',service)
    if d%5==0 and stock[(ag,'PIECE-FILTRE')]>=1:
        vid=random.choice(avail);stock[(ag,'PIECE-FILTRE')]-=1;seq['issue']+=1;ref=f'SOR-{seq["issue"]:06d}';amount=40000
        rows['consommations_stock'].append(dict(sortie_id=ref,date=daystr(d),agence=ag,article='PIECE-FILTRE',quantite=1,cout=amount,vehicule=vid,service='GARAGE'))
        rows['mouvements_stock'].append(dict(mouvement_id=f'STK-{len(rows["mouvements_stock"])+1:06d}',date=daystr(d),type='CONSOMMATION',article_id='PIECE-FILTRE',agence=ag,depot=f'{ag}-DEPOT',quantite_entree=0,quantite_sortie=1,vehicule=vid,document=ref))
        entry(daystr(d),'STOCK',ref,[('60-S',amount,0),('31-DEMO',0,amount)],'CONSOMMATION_STOCK',ref,ag,vid,'GARAGE')

# Paie 300 employés, après activités du mois. Déduction 5%/charges patronales 10% FICTIVES.
# Valeurs fictives, ne correspondent pas à CNPS/IRPP réels. Paie + règlement bancaire.
for e in rows['employes']:
    emp=e['employe_id'];ag=e['agence'];veh=e['vehicule_rattache'];gross=salaries[emp]
    deduct=round(gross*.05);employer=round(gross*.10);net=gross-deduct
    payslip=f'PAIE-202609-{emp}'
    rows['bulletins_paie'].append(dict(bulletin_id=payslip,employe_id=emp,mois='2026-09',brut=gross,retenue_demo_5pct=deduct,net_paye=net,charges_employeur_demo_10pct=employer,date_paiement='2026-09-30',mode='BANQUE',note='Barèmes fictifs; pas un moteur CNPS/IRPP'))
    entry('2026-09-30','PAIE',payslip,[('661-DEMO',gross,0),('664-DEMO',employer,0),('422-DEMO',0,net),('431-DEMO',0,deduct+employer)],'BULLETIN_PAIE',payslip,ag,veh,'RH')
    entry('2026-09-30','BANQUE','VIR-'+payslip,[('422-DEMO',net,0),('521-DEMO',0,net)],'PAIEMENT_SALAIRE','VIR-'+payslip,ag)

# Redevances partenaires: calcul basé sur recettes - charges analytiques déjà issues GA (avant redevance).
for vid in sorted(vehicle_owner):
    pid=vehicle_owner[vid]
    if pid=='COMPAGNIE':continue
    pre=vehicle_products[vid]-vehicle_costs[vid]
    due=max(0,round(pre*.70))
    ref=f'REDEV-202609-{vid}'
    rows['situations_partenaires'].append(dict(contrat_id=f'CTR-{vid}',vehicule=vid,partenaire=pid,produits_vehicule=vehicle_products[vid],charges_directes_et_paie=vehicle_costs[vid],marge_avant_redevance=pre,taux_contractuel_demo=0.70,redevance_reconnue=due,versé=round(due*.60),reste_du=due-round(due*.60)))
    if due:
        entry('2026-09-30','OD',ref,[('63-PART',due,0),('467-DEMO',0,due)],'REDEVANCE_PARTENAIRE',ref,vehicle_ag[vid],vid,'PARTENAIRES')
        paid=round(due*.60)
        entry('2026-09-30','BANQUE','VIR-'+ref,[('467-DEMO',paid,0),('521-DEMO',0,paid)],'REGLEMENT_PARTENAIRE','VIR-'+ref,vehicle_ag[vid],vid,'PARTENAIRES')
        partner_due[pid]+=due-paid

# résumé véhicules et agences, comptes, contrôles
for vid in sorted(vehicle_ag):
    rows['etat_vehicules'].append(dict(vehicule=vid,gamme=vehicle_range[vid],agence_attache=vehicle_ag[vid],proprietaire=vehicle_owner[vid],produits_comptabilises=vehicle_products[vid],charges_comptabilisees=vehicle_costs[vid],resultat_partiel_comptable=vehicle_products[vid]-vehicle_costs[vid],note='Certaines charges générales non allouées aux véhicules'))
for aid,city,_,_ in agencies:
    rows['synthese_agences'].append(dict(agence=aid,ville=city,billets=sum(int(t['tarif']) for t in rows['billets'] if t['agence_vente']==aid),colis=sum(int(c['montant']) for c in rows['colis'] if c['agence_depart']==aid),salaires_bruts=sum(salaries[e['employe_id']] for e in rows['employes'] if e['agence']==aid),voyages_realises=sum(1 for v in rows['voyages'] if v['agence_exploitation']==aid),personnel=counts[aid]))
for code in accounts:
  debit=sum(int(x['debit']) for x in rows['ecritures_lignes'] if x['compte']==code)
  credit=sum(int(x['credit']) for x in rows['ecritures_lignes'] if x['compte']==code)
  rows['balance_generale_demo'].append(dict(compte=code,intitule=accounts[code],total_debit=debit,total_credit=credit,solde_debiteur=max(0,debit-credit),solde_crediteur=max(0,credit-debit)))
# Journal simplifié d'un jour & agence. Distinction recette économique et caisse.
for d in range(1,31):
 for aid,city,_,_ in agencies:
   tickets_rev=sum(int(t['tarif']) for t in rows['billets'] if t['agence_exploitation']==aid and t['date_depart']==daystr(d))
   tickets_paid=sum(int(t['tarif']) for t in rows['billets'] if t['agence_vente']==aid and t['date_vente']==daystr(d))
   packages=sum(int(c['montant']) for c in rows['colis'] if c['agence_depart']==aid and c['date_acceptation']==daystr(d))
   costs=sum(int(x['montant']) for x in rows['depenses'] if x['agence']==aid and x['date']==daystr(d))
   cash_in=sum(int(t['tarif']) for t in rows['billets'] if t['agence_vente']==aid and t['date_vente']==daystr(d) and t['moyen_paiement']=='ESPECES')+sum(int(c['montant']) for c in rows['colis'] if c['agence_depart']==aid and c['date_acceptation']==daystr(d) and c['mode']=='ESPECES')
   mob_in=tickets_paid+packages-cash_in
   rows['rj_agences_synthese'].append(dict(date=daystr(d),agence=aid,ville=city,billetterie_exploitation=tickets_rev,billetterie_encaissee_sur_place=tickets_paid,recettes_colis_encaissees=packages,decaissements_route=costi if (costi:=costs) else 0,entrees_especes=cash_in,entrees_mobile=mob_in,note='Rapport exploitation et caisse séparés; dépenses autres services non reprises dans cette vue synthétique'))

# vérifier les grands invariants mathématiques
assert sum(bal.values())==0
assert all(int(x['debit'])==int(x['credit']) for x in rows['ecritures_entetes'])
assert len(rows['vehicules'])==65 and sum(v['transport']=='VOYAGEURS' for v in rows['vehicules'])==60
assert sum(v['proprietaire']!='COMPAGNIE' for v in rows['vehicules'])==15
assert len(rows['bulletins_paie'])==300
assert len(rows['rj_agences_synthese'])==240
assert sum(int(t['tarif']) for t in rows['billets'])==sum(int(t['produits_comptabilises']) for t in rows['etat_vehicules'])-sum(int(c['montant']) for c in rows['colis'])
assert sum(int(x['total_debit']) for x in rows['balance_generale_demo'])==sum(int(x['total_credit']) for x in rows['balance_generale_demo'])
assert all(q>=0 for q in stock.values()),[(k,v) for k,v in stock.items() if v<0]
# chaque ventilation réf GA comptabilisée
lineids={l['ligne_id'] for l in rows['ecritures_lignes']}
assert all(a['source_gl_line_id'] in lineids for a in rows['ventilations_analytiques'])
# soldes de stock quantités
for (ag,sku),q in sorted(stock.items()):rows['stock_final'].append(dict(agence=ag,article=sku,quantite_fin=q,cout_unitaire_demo={x[0]:x[2] for x in items}[sku],valeur_fin=q*{x[0]:x[2] for x in items}[sku]))

for key,r in rows.items():
    if not r:continue
    with (BASE/f'{key}.csv').open('w',newline='',encoding='utf-8-sig') as f:
      w=csv.DictWriter(f,fieldnames=list(r[0].keys()),delimiter=';');w.writeheader();w.writerows(r)
metrics={
 'periode':'2026-09-01 / 2026-09-30', 'seed':SEED,
 'agences':len(rows['agences']),'employes':len(rows['employes']), 'vehicules_voyageurs':60, 'vehicules_courrier':5,'vehicules_partenaires':15,'partenaires':10,
 'voyages':len(rows['voyages']),'billets':len(rows['billets']),'colis':len(rows['colis']),
 'demandes_achat':len(rows['demandes_achat']), 'bons_commande':len(rows['bons_commande']), 'factures_fournisseurs':len(rows['factures_fournisseurs']),
 'bulletins_paie':len(rows['bulletins_paie']),
 'ventilations':len(rows['ventilations_analytiques']), 'lignes_gl':len(rows['ecritures_lignes']),
 'recettes_billets':sum(int(t['tarif']) for t in rows['billets']), 'recettes_colis':sum(int(c['montant']) for c in rows['colis']),
 'frais_carburant_peage':sum(int(x['montant']) for x in rows['depenses']),
 'brut_paie':sum(int(x['brut']) for x in rows['bulletins_paie']), 'net_paie':sum(int(x['net_paye']) for x in rows['bulletins_paie']),
 'charges_employeur_demo':sum(int(x['charges_employeur_demo_10pct']) for x in rows['bulletins_paie']),
 'redevances_partenaires':sum(int(x['redevance_reconnue']) for x in rows['situations_partenaires']),
 'solde_partenaires_restant':sum(int(x['reste_du']) for x in rows['situations_partenaires']),
 'solde_fournisseurs':-bal['401-DEMO'],'solde_compte_stock':bal['31-DEMO'],
 'solde_compte_bank':bal['521-DEMO'],'solde_compte_cash_global':bal['5711-DEMO'],
 'solde_compte_mobile':bal['552-DEMO'],
 'total_debit':sum(int(x['debit']) for x in rows['ecritures_lignes']),
 'total_credit':sum(int(x['credit']) for x in rows['ecritures_lignes']),
 'resultat_societe_avant_impots_hors_amortissement':sum(int(x['credit'])-int(x['debit']) for x in rows['ecritures_lignes'] if x['compte'] in REV)-sum(int(x['debit'])-int(x['credit']) for x in rows['ecritures_lignes'] if x['compte'] in CHARGES),
}
with (BASE/'METRIQUES_ET_CONTROLES.json').open('w',encoding='utf-8') as f:json.dump(metrics,f,ensure_ascii=False,indent=2)
with (BASE/'CONTROLE_RUN.txt').open('w',encoding='utf-8') as f:
    f.write('Simulation fictive SEPTEMBRE 2026; seed=20260926\nTous journaux équilibrés; aucune ligne analytique sans ligne GL.\n')
    for k,v in metrics.items():f.write(f'{k}: {v}\n')
print(json.dumps(metrics,ensure_ascii=False,indent=2))
