#!/usr/bin/env python3
"""Compare deux CSV de métadonnées d'une même extraction SQL (sans connexion SQL).
Ex : python comparer_catalogues.py --avant base_v10_columns.csv --apres base_v12_columns.csv --sortie diff.csv
Champs attendus : schema_name, table_name, column_name, sql_type, max_length, precision, scale,
                   is_nullable, is_identity, is_computed (présents dans 01_INVENTAIRE...sql).
Ne suppose pas les différences de version avant exécution.
"""
import argparse,csv,sys
from pathlib import Path
KEY=('schema_name','table_name','column_name')
VALUES=('sql_type','max_length','precision','scale','is_nullable','is_identity','is_computed')
def load(path):
 with open(path,encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  req=set(KEY+VALUES)
  if not req.issubset(set(reader.fieldnames or [])):
   raise ValueError('Colonnes requises absentes: '+str(sorted(req-set(reader.fieldnames or []))))
  rows={}
  for row in reader:
   key=tuple(row[k].strip().upper() for k in KEY)
   if key in rows: raise ValueError('Clé répétée dans '+str(path)+': '+str(key))
   rows[key]=row
  return rows
def diff(old,new):
 a,b=load(old),load(new)
 result=[]
 for k in sorted(set(a)|set(b)):
  if k not in a: result.append([*k,'AJOUT', '', '', '']);continue
  if k not in b: result.append([*k,'RETRAIT', '', '', '']);continue
  for col in VALUES:
   v1=a[k][col].strip();v2=b[k][col].strip()
   if v1!=v2: result.append([*k,'MODIFICATION',col,v1,v2])
 return result
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--avant',type=Path,required=True);p.add_argument('--apres',type=Path,required=True);p.add_argument('--sortie',type=Path,required=True)
 args=p.parse_args(argv); results=diff(args.avant,args.apres)
 args.sortie.parent.mkdir(parents=True,exist_ok=True)
 with args.sortie.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow([*KEY,'change_type','attribute','before','after']);w.writerows(results)
 print('Divergences:',len(results),'—',args.sortie)
if __name__=='__main__':main()
