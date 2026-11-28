@echo off
REM Poste SERVEUR de l agence : les autres ordinateurs du reseau local utilisent le logiciel depuis leur navigateur
chcp 65001 >nul
cd /d "%~dp0"
title ERP OHADA - SERVEUR de l agence (ne pas fermer)
if not exist logiciel\.env (
  echo Le logiciel n est pas encore installe : lancez d abord 1-INSTALLER.bat
  pause
  exit /b 1
)
"python\python.exe" outils\reseau.py
cd logiciel
start "" cmd /c "timeout /t 4 >nul & start http://127.0.0.1:8000"
"..\python\python.exe" -m waitress --listen=0.0.0.0:8000 --threads=16 erp.wsgi:application
pause
