#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQL Server: exports ONLY schema metadata, never business values or writes.

Requirements (Windows target): pip install pyodbc
Example (Windows, login SQL read-only):
  python export_sql_metadata.py --server SQLSERVER\\SAGE --database COMPANY_GCM --out dossier_meta
  python export_sql_metadata.py --server SQLSERVER --database COMPANY_MAE --driver "ODBC Driver 18 for SQL Server" --out meta

For SQL authentication, use environment variables SAGE_SQL_USER and SAGE_SQL_PASSWORD,
not command-line parameters. Prefer integrated security (Trusted_Connection). Never use
sysadmin credential. SQL ApplicationIntent=ReadOnly is a routing hint NOT a permission!
"""
import argparse, csv, json, os, pathlib, re, sys
from datetime import datetime, timezone

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--server',required=True)
    a.add_argument('--database',required=True)
    a.add_argument('--out',required=True)
    a.add_argument('--driver',default='ODBC Driver 17 for SQL Server')
    a.add_argument('--trust-server-certificate',action='store_true',help='Only on controlled LAN with approved cert policy')
    args=a.parse_args()
    try: import pyodbc
    except ImportError: raise SystemExit('Installer pyodbc (pip install pyodbc) sur Windows')
    if not re.fullmatch(r'[\w\- .\\]+',args.server): raise SystemExit('Nom serveur inhabituel')
    if not re.fullmatch(r'[\w\- .]+',args.database): raise SystemExit('Nom base inhabituel')
    user=os.getenv('SAGE_SQL_USER')
    pw=os.getenv('SAGE_SQL_PASSWORD')
    if bool(user)!=bool(pw): raise SystemExit('SAGE_SQL_USER et SAGE_SQL_PASSWORD requis ensemble')
    parts=[f'DRIVER={{{args.driver}}}', f'SERVER={args.server}', f'DATABASE={args.database}', 'ApplicationIntent=ReadOnly', 'Connection Timeout=10', 'Encrypt=yes' ]
    parts.append('TrustServerCertificate=yes' if args.trust_server_certificate else 'TrustServerCertificate=no')
    if user: parts.extend([f'UID={user}', f'PWD={pw}'])
    else: parts.append('Trusted_Connection=yes')
    conn=pyodbc.connect(';'.join(parts),timeout=20,autocommit=True)
    cr=conn.cursor()
    # Defense in depth: SET XACT_ABORT does not modify business data; read metadata ONLY.
    # SQL Server system catalog views report table, column, PK, FK, index, defaults. No SELECT *.
    queries={
    'tables': """SELECT s.name AS schema_name,t.name AS table_name, t.type_desc, t.create_date, t.modify_date
    FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id
    ORDER BY s.name,t.name""",
    'columns': """SELECT s.name AS schema_name,t.name AS table_name,c.column_id,c.name AS column_name,
      ty.name AS sql_type,c.max_length,c.precision,c.scale,c.is_nullable,c.is_identity,c.is_computed,
      dc.definition AS default_expression,ep.value AS description
    FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id
    JOIN sys.columns c ON c.object_id=t.object_id JOIN sys.types ty ON ty.user_type_id=c.user_type_id
    LEFT JOIN sys.default_constraints dc ON c.default_object_id=dc.object_id
    LEFT JOIN sys.extended_properties ep ON ep.major_id=t.object_id AND ep.minor_id=c.column_id AND ep.name='MS_Description'
    ORDER BY s.name,t.name,c.column_id""",
    'indexes': """SELECT s.name AS schema_name,t.name AS table_name,i.name AS index_name,i.type_desc,
      i.is_unique,i.is_primary_key,ic.key_ordinal,c.name AS column_name,ic.is_included_column
    FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id
    JOIN sys.indexes i ON t.object_id=i.object_id
    JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id
    JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
    WHERE i.is_hypothetical=0 ORDER BY s.name,t.name,i.name,ic.key_ordinal,c.name""",
    'foreign_keys': """SELECT sch.name AS schema_name, t.name AS table_name, fk.name AS fk_name,
    pc.name AS from_column, rsch.name AS referenced_schema,rt.name AS referenced_table,rc.name AS referenced_column,
    fkc.constraint_column_id
    FROM sys.foreign_keys fk
    JOIN sys.tables t ON t.object_id=fk.parent_object_id
    JOIN sys.schemas sch ON sch.schema_id=t.schema_id
    JOIN sys.tables rt ON rt.object_id=fk.referenced_object_id
    JOIN sys.schemas rsch ON rsch.schema_id=rt.schema_id
    JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id=fk.object_id
    JOIN sys.columns pc ON pc.object_id=t.object_id AND pc.column_id=fkc.parent_column_id
    JOIN sys.columns rc ON rc.object_id=rt.object_id AND rc.column_id=fkc.referenced_column_id
    ORDER BY sch.name,t.name,fk.name,fkc.constraint_column_id"""
    }
    dest=pathlib.Path(args.out);dest.mkdir(parents=True,exist_ok=True)
    counts={}
    for key,q in queries.items():
        cr.execute(q)
        headings=[x[0] for x in cr.description]
        file=dest/f'{key}.csv'
        n=0
        with file.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f);w.writerow(headings)
            for row in cr:
                w.writerow(['' if x is None else str(x) for x in row]);n+=1
        counts[key]=n
    info={'database':args.database,'server_name_masked':'[non exporté]',
          'sampled_at_utc':datetime.now(timezone.utc).isoformat(),
          'scope':'schema system metadata only; no customer or transaction rows',
          'counts':counts, 'warning':'Métadonnées SQL ≠ règles métier, onglets et actions. Ne PAS écrire dans Sage.'}
    (dest/'manifest.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    conn.close()
    print(json.dumps(info,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
