#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows registry read-only scan of registered Sage COM ProgIDs and TypeLib paths.
python inventaire_com_windows.py --out om_registry.json
Uses only winreg/stdlib. Does not instantiate a COM object or open Sage.
A partial registry list is NOT proof of all SDK classes: consult official manual + typelib.
"""
import argparse,sys,json,re
from pathlib import Path
from datetime import datetime,timezone

def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--out',required=True); a=a.parse_args()
 if sys.platform!='win32':raise SystemExit('Windows uniquement')
 import winreg
 # HKEY_CLASSES_ROOT merged view may hide per-user registration. Scan both x86/x64.
 records=[]
 for wow in [winreg.KEY_WOW64_32KEY,winreg.KEY_WOW64_64KEY]:
  try:r=winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,'',0,winreg.KEY_READ|wow)
  except OSError:continue
  j=0
  while True:
   try:key=winreg.EnumKey(r,j);j+=1
   except OSError:break
   if 'sage' not in key.lower() and not any(x in key.lower() for x in ['bscpta','bscial','objetsmetiers']):continue
   if not re.fullmatch(r'[A-Za-z0-9._ -]{1,150}',key):continue
   try:
    with winreg.OpenKey(r,key+'\\CLSID') as k: cls=winreg.QueryValueEx(k,'')[0]
   except OSError:cls=None
   records.append({'registry_view':'32' if wow==winreg.KEY_WOW64_32KEY else '64',
                   'ProgID_candidate':key,'CLSID':cls})
 manifest={'created_utc':datetime.now(timezone.utc).isoformat(),
           'note':'Indices de composants COM, pas preuve d’interfaces ou méthodes disponibles. Vérifier droits et SDK.',
           'entries':records}
 out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print(len(records),'entrées de registre candidates dans',out)
if __name__=='__main__':main()
