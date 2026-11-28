#!/usr/bin/env python3
"""Tests reproductibles du mini-scénario GA → analytique → compte propriétaire."""
from pathlib import Path
import csv
from collections import defaultdict
from decimal import Decimal
P=Path(__file__).resolve().parent.parent/'examples'
def read(name):
 with (P/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def D(x):return Decimal(str(x))
gl=read('ecritures_gl.csv');an=read('ventilations_gl.csv');releve=read('releve_proprietaire.csv');case=read('cas_proprietaire_fixe_variable.csv')[0]
checks=defaultdict(lambda:[Decimal(0),Decimal(0)])
for r in gl:
 assert r['statut']=='POSTED'
 checks[r['ecriture_id']][0]+=D(r['debit']);checks[r['ecriture_id']][1]+=D(r['credit'])
assert all(d==c for d,c in checks.values()), checks
assert sum(D(r['debit']) for r in gl)==sum(D(r['credit']) for r in gl)
by_line={r['ligne_gl_id']:r for r in gl}
assert len(by_line)==len(gl)
for a in an:
 assert a['source_gl_line_id'] in by_line
 r=by_line[a['source_gl_line_id']]
 assert r['statut']=='POSTED' and a['statut_source']=='POSTED'
 assert D(a['montant'])==abs(D(r['debit'])-D(r['credit']))
assert len(an)==4
revenue=sum(D(a['montant']) for a in an if a['type']=='PRODUIT')
expense=sum(D(a['montant']) for a in an if a['type']!='PRODUIT')
assert revenue==D('1000000') and expense==D('730000')
assert revenue-expense==D(case['resultat_vehicule_apres_owner'])==D('270000')
owner_due=sum(D(r['droit_du']) for r in releve)
owner_paid=sum(D(r['versement']) for r in releve)
assert owner_due==D(case['droit_total'])==D('330000')
assert owner_paid==D(case['montant_fixe_verse'])+D(case['retrait_variable_verse'])==D('250000')
assert owner_due-owner_paid==D(case['reste_du'])==D(releve[-1]['solde_du'])==D('80000')
owner_credit=sum(D(r['credit']) for r in gl if r['compte_demo']=='46-OWNER-DEMO')
owner_debit=sum(D(r['debit']) for r in gl if r['compte_demo']=='46-OWNER-DEMO')
assert owner_credit-owner_debit==D('80000')
roles=read('roles_tiers.csv')
assert {'PROPRIETAIRE_VEHICULE','FOURNISSEUR'}.issubset({r['role_type'] for r in roles if r['party_id']=='PTY-001'})
assert len({r['compte_auxiliaire_exemple'] for r in roles if r['party_id']=='PTY-001'})==2
print('OK — écritures GA équilibrées, imputations toutes sourcées, résultat véhicule 270 000 FCFA, droits 330 000 FCFA, payé 250 000 FCFA, solde dû 80 000 FCFA, rôle fournisseur séparé.')
