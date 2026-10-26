@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0logiciel"
title ERP Transport - Simulation pluri-mois (base fictive)
if not exist "..\python\python.exe" (
 echo Installer d'abord le paquet Windows avec 1-INSTALLER.bat.
 pause
 exit /b 1
)
set "DB_ENGINE=sqlite"
set "SQLITE_FICHIER=simulation_plurimois.sqlite3"
set "CONTROLE_HEURE_DEPART=0"
if exist "simulation_plurimois.sqlite3" (
 echo Une simulation pluri-mois existe deja. Arret pour ne rien ecraser.
 echo Faire une SAUVEGARDE et utiliser un autre nom de base ou l'archiver manuellement.
 pause
 exit /b 1
)
echo Simulation fictive 8 agences, 300 employes, 60 cars, 5 camions courrier.
set /p "MOIS=Premier mois AAAA-MM [2026-01] : "
if "%MOIS%"=="" set "MOIS=2026-01"
set /p "NOMBRE=Nombre de mois (1 a 36) [3] : "
if "%NOMBRE%"=="" set "NOMBRE=3"
set /p "ECHELLE=Echelle voyageurs/colis (0.05 a 1) [0.1] : "
if "%ECHELLE%"=="" set "ECHELLE=0.1"
"..\python\python.exe" manage.py migrate --noinput
if errorlevel 1 goto erreur
"..\python\python.exe" manage.py simulation_pluri_mois --mois %MOIS% --nombre-mois %NOMBRE% --echelle %ECHELLE% --rapport "%~dp0BILAN-SIMULATION-PLURI-MOIS.md" --rapport-json "%~dp0BILAN-SIMULATION-PLURI-MOIS.json"
if errorlevel 1 goto erreur
"..\python\python.exe" manage.py createsuperuser
if errorlevel 1 goto erreur
echo.
echo Rapports : BILAN-SIMULATION-PLURI-MOIS.md et .json
echo Demarrage local http://127.0.0.1:8111
start "" cmd /c "timeout /t 4 >nul & start http://127.0.0.1:8111"
"..\python\python.exe" -m waitress --listen=127.0.0.1:8111 --threads=8 erp.wsgi:application
pause
exit /b 0
:erreur
echo La simulation s'est arretee. La base de test est conservee pour diagnostic.
echo NE PAS supprimer de base reelle. Consulter les messages et les journaux.
pause
exit /b 1
