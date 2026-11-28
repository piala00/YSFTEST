#!/usr/bin/env python3
"""Compare deux exports CSV de métadonnées; aucune connexion ni écriture SQL."""
import argparse,csv,json
from pathlib import Path

def read(path,keys):
    with open(path,encoding='utf-8-sig',newline='') as fh:
        rd=csv.DictReader(fh)
        if not set(keys).issubset(rd.fieldnames or []):
            raise ValueError('Colonnes clefs manquantes: '+','.join(set(keys)-set(rd.fieldnames or [])))
        rows={}
        for r in rd:
            k=tuple(r[c] for c in keys)
            if k in rows: raise ValueError('Clef dupliquee: '+str(k))
            rows[k]=r
        return rows

def diff(before,after,keys):
    b=read(before,keys);a=read(after,keys);result=[]
    for key in sorted(set(b)|set(a)):
        if key not in b: result.append({'statut':'AJOUT','cle':list(key),'avant':None,'apres':a[key]})
        elif key not in a: result.append({'statut':'RETRAIT','cle':list(key),'avant':b[key],'apres':None})
        elif b[key]!=a[key]:result.append({'statut':'MODIFICATION','cle':list(key),'avant':b[key],'apres':a[key]})
    return result

if __name__=='__main__':
    pa=argparse.ArgumentParser()
    pa.add_argument('avant');pa.add_argument('apres');pa.add_argument('--cles',required=True,
                    help='Colonnes communes separees par virgules : schema_name,objet,colonne')
    pa.add_argument('--sortie',required=True)
    ar=pa.parse_args()
    output=diff(ar.avant,ar.apres,[s.strip() for s in ar.cles.split(',')])
    Path(ar.sortie).write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Ecarts:',len(output))
