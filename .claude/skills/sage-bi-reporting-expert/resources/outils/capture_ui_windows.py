#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""READ-ONLY inventory of UI Automation elements of an ALREADY OPEN Sage window.
Requirements on Windows: pip install pywinauto
Example: python capture_ui_windows.py --title "Sage 100" --output sage_capture.json --version V12.20
No clicks, keystrokes, data entry or screenshots are performed. Does not export
user-entered values (edit box values remain omitted). Some classic windows expose
few accessible elements; in that case manually document screenshots *redacted*.
"""
import argparse,json,sys,re
from datetime import datetime,timezone
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--title',required=True,help='Substring of visible window title (e.g. Sage 100)')
 p.add_argument('--version',required=True);p.add_argument('--edition',default='inconnue')
 p.add_argument('--product',default='Sage 100');p.add_argument('--output',required=True)
 p.add_argument('--max-nodes',type=int,default=3500)
 a=p.parse_args()
 if sys.platform!='win32':raise SystemExit('Cet inventaire UIA s’exécute uniquement sous Windows')
 try:from pywinauto import Desktop
 except ImportError:raise SystemExit('Installer pywinauto : pip install pywinauto')
 def clean(t):
  t=str(t or '').strip()
  # Avoid printing user data: placeholders for text inputs; button/label titles only.
  return t[:128]
 results=[]; count=0
 for w in Desktop(backend='uia').windows():
  try:
   if a.title.lower() not in w.window_text().lower():continue
   win={'window_title':'[masqué pour confidentialité]' ,'controls':[]}
   # Collect names only for structural elements. Names of Edit cells and DataItems
   # can reflect customer data, so redact those entirely.
   for el in w.descendants():
    if count>=a.max_nodes:break
    info=el.element_info
    kind=str(getattr(info,'control_type','') or '')
    name='' if kind in ('Edit','DataItem','Text','Document','ListItem') else clean(getattr(info,'name',''))
    wid=clean(getattr(info,'automation_id',''))
    cls=clean(getattr(info,'class_name',''))
    win['controls'].append({'type':kind,'name':name,'automation_id':wid,'class':cls,
                            'name_redacted':kind in ('Edit','DataItem','Text','Document','ListItem')})
    count+=1
   results.append(win)
  except Exception as ex: results.append({'window_error_type':type(ex).__name__})
 output={'product':a.product,'version':a.version,'edition':a.edition,
         'timestamp_utc':datetime.now(timezone.utc).isoformat(),
         'scope':'UIA structural metadata only; text entry and row labels redacted',
         'warnings':['No interaction performed','Some Win32 Sage classic UI controls do not expose accessibility metadata',
                     'Button labels may contain custom labels; manually inspect for privacy'],
         'windows':results,'node_count':count}
 dst=Path(a.output);dst.parent.mkdir(parents=True,exist_ok=True)
 dst.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Fenêtres trouvées:',len(results),'contrôles:',count,'fichier:',dst)
if __name__=='__main__':main()
