#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare schema metadata extracted on TWO Sage versions. Does not contact databases.
python diff_sql_schemas.py --old meta_V5 --new meta_V12 --out diff.csv
"""
import argparse,csv,os,json
from pathlib import Path

def load(d):
    p=Path(d)/'columns.csv'
    with p.open('r',encoding='utf-8-sig',newline='') as f:
        data=list(csv.DictReader(f))
    return {(r['schema_name'],r['table_name'],r['column_name']):r for r in data}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--old',required=True);p.add_argument('--new',required=True);p.add_argument('--out',required=True)
 a=p.parse_args(); old=load(a.old); new=load(a.new); rows=[]
 for k in sorted(old.keys()|new.keys()):
  prev=old.get(k); nxt=new.get(k)
  if not prev:status='AJOUTÉ'
  elif not nxt:status='SUPPRIMÉ'
  else:
   keys=['sql_type','max_length','precision','scale','is_nullable','is_identity','is_computed','default_expression']
   diffs=[x for x in keys if prev.get(x)!=nxt.get(x)]
   status='MODIFIÉ: '+', '.join(diffs) if diffs else 'IDENTIQUE'
  if status!='IDENTIQUE':rows.append({'schema':k[0],'table':k[1],'column':k[2],
                'status':status,'ancien':json.dumps(prev,ensure_ascii=False),'nouveau':json.dumps(nxt,ensure_ascii=False)})
 dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=['schema','table','column','status','ancien','nouveau']);w.writeheader();w.writerows(rows)
 print(f'{len(rows)} différences structurelles : {dest}')
 print('Attention : même structure != même règle métier; vérifier Sage et manuels.')
if __name__=='__main__':main()
