#!/usr/bin/env python3
"""Contrôles de cohérence sur les fixtures CSV uniquement, sans base réelle."""
from pathlib import Path
import csv,json,collections,datetime
D=Path(__file__).resolve().parent.parent/'examples'/'demo_2026_09'

def read(name):
    with (D/(name+'.csv')).open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f,delimiter=';'))

def integer(v):return int(v or 0)
A=read('agences');E=read('employes');V=read('vehicules');T=read('voyages');B=read('billets');C=read('colis'); P=read('partenaires');PS=read('situations_partenaires');H=read('ecritures_entetes');L=read('ecritures_lignes'); AN=read('ventilations_analytiques');PA=read('bulletins_paie');BC=read('bons_commande');BR=read('receptions');F=read('factures_fournisseurs');ST=read('mouvements_stock');SFIN=read('stock_final');R=read('rj_agences_synthese');bal=read('balance_generale_demo')
metrics=json.loads((D/'METRIQUES_ET_CONTROLES.json').read_text(encoding='utf-8'))
assert len(A)==8 and len(E)==300 and len(V)==65 and len(P)==10
assert sum(v['transport']=='VOYAGEURS' for v in V)==60
assert sum(v['transport']=='COURRIER' for v in V)==5
assert sum(v['proprietaire']!='COMPAGNIE' for v in V)==15
assert sum(v['gamme']=='VIP' for v in V)==24
assert sum(v['gamme']=='CLASSIQUE' for v in V)==36
assert len(PA)==300 and len(BC)==len(BR)==len(F)==32
assert len(R)==8*30
assert {r['date'] for r in R}=={f'2026-09-{d:02d}' for d in range(1,31)}
assert {p['date_paiement'] for p in PA}=={'2026-09-30'}
assert all(integer(p['brut'])==integer(p['retenue_demo_5pct'])+integer(p['net_paye']) for p in PA)
vehicles={v['vehicule_id']:v for v in V};trips={t['voyage_id']:t for t in T}
seatset=set()
for b in B:
    assert b['voyage_id'] in trips and b['vehicule_id']==trips[b['voyage_id']]['vehicule_id']
    assert b['date_depart']==trips[b['voyage_id']]['date_depart']
    assert 1<=integer(b['place'])<=integer(trips[b['voyage_id']]['capacite'])
    key=(b['voyage_id'],b['place']);assert key not in seatset;seatset.add(key)
for t in T:
    assert integer(t['voyageurs'])==sum(b['voyage_id']==t['voyage_id'] for b in B)
assert all(c['vehicule_transporteur'] in vehicles for c in C)
refs={h['ecriture_id']:h for h in H};glids={l['ligne_id']:l for l in L}
assert len(glids)==len(L)
groups=collections.defaultdict(lambda:[0,0]); analytic=collections.defaultdict(int)
for l in L:
    assert l['ecriture_id'] in refs and l['statut']=='COMPTABILISE'
    groups[l['ecriture_id']][0]+=integer(l['debit'])
    groups[l['ecriture_id']][1]+=integer(l['credit'])
assert all(d==c for d,c in groups.values())
assert sum(integer(l['debit']) for l in L)==sum(integer(l['credit']) for l in L)==metrics['total_debit']
for v in AN:
    line=glids[v['source_gl_line_id']]
    assert line['ecriture_id']==v['source_gl_entry_id']
    assert v['statut']=='SOURCE_COMPTABILISEE'
    analytic[line['ligne_id']]+=integer(v['montant_signe_resultat'])
for l in L:
    if l['compte'] in {'706-V','706-C','605-F','63-PE','624-R','60-S','661-DEMO','664-DEMO','63-PART'}:
        assert analytic[l['ligne_id']]==integer(l['credit'])-integer(l['debit']),(l,analytic[l['ligne_id']])
    else:assert l['ligne_id'] not in analytic
assert sum(analytic.values())==metrics['resultat_societe_avant_impots_hors_amortissement']
assert sum(integer(b['tarif']) for b in B)==metrics['recettes_billets']
assert sum(integer(c['montant']) for c in C)==metrics['recettes_colis']
# Facture BC / BR présent, total lignes = total facture
po_lines=collections.Counter()
for l in read('lignes_achats'):po_lines[l['bc_id']]+=integer(l['total'])
po_ids={p['bc_id'] for p in BC}
for f in F:assert f['bc_id'] in po_ids and po_lines[f['bc_id']]==integer(f['montant_ht_demo'])
# Stocks : la somme quantité des entrées - sorties donne le stock final pour chaque article/agence.
qty=collections.Counter()
for st in ST:
    if st['type']=='EQUIPEMENT_IMMOBILISE':continue
    qty[(st['agence'],st['article_id'])]+=integer(st['quantite_entree'])-integer(st['quantite_sortie'])
assert all(v>=0 for v in qty.values())
for fin in SFIN:
    assert qty[(fin['agence'],fin['article'])]==integer(fin['quantite_fin'])
assert len(SFIN)==len(qty)
assert sum(integer(p['reste_du']) for p in PS)==metrics['solde_partenaires_restant']
assert sum(integer(p['redevance_reconnue']) for p in PS)==metrics['redevances_partenaires']
assert sum(integer(x['solde_debiteur']) for x in bal)==sum(integer(x['solde_crediteur']) for x in bal)
assert sum(integer(x['total_debit']) for x in bal)==sum(integer(x['total_credit']) for x in bal)
print('VALIDATION OK: 8 agences, 300 salaries, 60 voyageurs dont 15 partenaires, 5 courriers.')
print(f"OK: {len(T)} voyages, {len(B)} billets sieges uniques, {len(C)} colis, {len(BC)} BC, {len(PA)} paies, {len(H)} ecritures GA, {len(AN)} allocations analytiques.")
print(f"OK: Debit = Credit = {metrics['total_debit']:,} FCFA. Toutes allocations financieres sourcées GA. 30 jours x 8 agences.")
print('ATTENTION: données et taux de paie fictifs, pas un paramétrage SYSCOHADA légal. Aucun test du vrai projet ERP n’est réalisé ici.')
