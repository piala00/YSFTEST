#!/usr/bin/env python3
"""Audit cohérence CSV / requêtes SQL, sans connexion externe."""
import csv,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(fn):
 with (root/'catalogues'/fn).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
tables=read('02_CATALOGUE_TABLES.csv');columns=read('03_CHAMPS_REPÈRES.csv');rels=read('04_RELATIONS_DOCUMENTAIRES.csv');types=read('05_CODES_DOCUMENTS.csv');sources=read('01_SOURCES.csv')
assert len(set((t['produit'],t['table']) for t in tables))==len(tables)
assert len(set((c['table'],c['champ']) for c in columns))==len(columns)
assert len(set((t['DO_Domaine'],t['DO_Type']) for t in types))==len(types)
settab={t['table'] for t in tables}
assert all(c['table'] in settab for c in columns)
assert all(r['table_source'] in settab and r['table_cible'] in settab for r in rels),[r for r in rels if r['table_source'] not in settab or r['table_cible'] not in settab]
assert all(c['preuve']=='S06-01' for c in columns)
for f in (root/'sql').glob('*.sql'):
 text=f.read_text(encoding='utf-8')
 clean=re.sub(r'/\*.*?\*/|--[^\n]*','',text,flags=re.S)
 # permitted no DML/DDL in actual statements (comments stripped)
 assert not re.search(r'\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC(?:UTE)?|DBCC)\b',clean,re.I),f
print('VALIDATION OK —',len(tables),'tables,',len(columns),'champs,',len(rels),'relations,',len(types),'codes documents')
