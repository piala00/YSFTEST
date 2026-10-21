#!/usr/bin/env python3
"""Export métadonnées SQL Server uniquement (6 SELECT, aucune donnée métier).
Nécessite pyodbc sous Windows et compte SQL sans permission d'écriture.
La chaîne de connexion DOIT venir de SAGE_SQL_CONN_RO, jamais d'arguments CLI ni de fichiers exportés.
Le script ne peut pas créer/modifier un objet SQL. Il écrit uniquement des CSV dans le dossier choisi.
"""
import os,csv,argparse,datetime,hashlib,json
from pathlib import Path
QUERIES={
 'objets':"""SELECT SCHEMA_NAME(o.schema_id) AS schema_name,o.name AS object_name,o.type_desc AS object_type,o.create_date,o.modify_date FROM sys.objects o WHERE o.is_ms_shipped=0 AND o.type IN ('U','V','P','TR','FN','IF','TF') ORDER BY schema_name,object_type,object_name""",
 'colonnes':"""SELECT SCHEMA_NAME(t.schema_id) AS schema_name,t.name AS table_name,c.column_id AS ordinal,c.name AS column_name,ty.name AS sql_type,c.max_length,c.precision,c.scale,c.is_nullable,c.is_identity,c.is_computed,c.collation_name FROM sys.tables t JOIN sys.columns c ON c.object_id=t.object_id JOIN sys.types ty ON ty.user_type_id=c.user_type_id WHERE t.is_ms_shipped=0 ORDER BY schema_name,table_name,ordinal""",
 'index':"""SELECT SCHEMA_NAME(t.schema_id) AS schema_name,t.name AS table_name,i.name AS index_name,i.type_desc AS index_type,i.is_unique,i.is_primary_key,ic.key_ordinal,ic.is_included_column,ic.is_descending_key,c.name AS column_name FROM sys.tables t JOIN sys.indexes i ON i.object_id=t.object_id JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id WHERE t.is_ms_shipped=0 AND i.is_hypothetical=0 AND i.name IS NOT NULL ORDER BY schema_name,table_name,index_name,ic.key_ordinal,c.name""",
 'cles_etrangeres':"""SELECT fk.name AS constraint_name,SCHEMA_NAME(tp.schema_id) AS from_schema,tp.name AS from_table,cp.name AS from_column,fkc.constraint_column_id AS position,SCHEMA_NAME(tr.schema_id) AS to_schema,tr.name AS to_table,cr.name AS to_column,fk.is_disabled,fk.is_not_trusted FROM sys.foreign_keys fk JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id=fk.object_id JOIN sys.tables tp ON tp.object_id=fkc.parent_object_id JOIN sys.columns cp ON cp.object_id=tp.object_id AND cp.column_id=fkc.parent_column_id JOIN sys.tables tr ON tr.object_id=fkc.referenced_object_id JOIN sys.columns cr ON cr.object_id=tr.object_id AND cr.column_id=fkc.referenced_column_id ORDER BY constraint_name,position""",
 'contraintes':"""SELECT SCHEMA_NAME(o.schema_id) AS schema_name,OBJECT_NAME(cc.parent_object_id) AS table_name,cc.name AS constraint_name,'CHECK' AS constraint_type FROM sys.check_constraints cc JOIN sys.objects o ON o.object_id=cc.parent_object_id UNION ALL SELECT SCHEMA_NAME(o.schema_id),OBJECT_NAME(dc.parent_object_id),dc.name,'DEFAULT' FROM sys.default_constraints dc JOIN sys.objects o ON o.object_id=dc.parent_object_id ORDER BY schema_name,table_name,constraint_name""",
 'dependances':"""SELECT SCHEMA_NAME(o.schema_id) AS schema_name,o.name AS referencing_object,d.referenced_schema_name,d.referenced_entity_name,d.referenced_id FROM sys.sql_expression_dependencies d JOIN sys.objects o ON o.object_id=d.referencing_id WHERE o.is_ms_shipped=0 ORDER BY schema_name,referencing_object"""
}
def run():
 p=argparse.ArgumentParser();p.add_argument('--dossier',required=True,type=Path);p.add_argument('--alias',default='BASE_TEST');args=p.parse_args()
 connstring=os.getenv('SAGE_SQL_CONN_RO','')
 if not connstring: p.error('SAGE_SQL_CONN_RO manquant. Utiliser un compte de lecture dédié.');
 # La chaîne de connexion provient uniquement de la variable d'environnement.
 import pyodbc
 args.dossier.mkdir(parents=True,exist_ok=True)
 with pyodbc.connect(connstring,timeout=15,autocommit=False) as cn:
  cn.timeout=45
  outputs=[]
  for nom,query in QUERIES.items():
   if not query.lstrip().upper().startswith('SELECT'): raise ValueError('Requête non-SELECT interdite')
   cur=cn.cursor(); cur.execute(query); cols=[x[0] for x in cur.description]
   target=args.dossier/(nom+'.csv')
   with target.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(cols)
    count=0
    for row in cur:
     w.writerow(['' if x is None else str(x) for x in row]);count+=1
   outputs.append({'dataset':nom,'rows':count,'filename':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
  cn.rollback() # aucune transaction métier modifiée; la connexion n'a réalisé que des SELECT.
  (args.dossier/'MANIFEST.json').write_text(json.dumps({'base_alias':args.alias,'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'METADONNEES_SEULEMENT','sorties':outputs},ensure_ascii=False,indent=2),encoding='utf-8')
 print('Extraction terminée :',args.dossier)
if __name__=='__main__':run()
