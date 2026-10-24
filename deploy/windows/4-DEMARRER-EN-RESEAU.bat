@echo off
REM Variante : ouvre l ERP aux autres postes du reseau local (http://NOM-DE-CE-PC:8000)
chcp 65001 >nul
cd /d "%~dp0logiciel"
title ERP OHADA (reseau local) - ne pas fermer
echo Les autres postes ouvrent http://%COMPUTERNAME%:8000 (autorisez le pare-feu Windows si demande)
start "" cmd /c "timeout /t 4 >/dev/null & start http://127.0.0.1:8000"
"..\python\python.exe" -m waitress --listen=0.0.0.0:8000 --threads=8 erp.wsgi:application
pause
