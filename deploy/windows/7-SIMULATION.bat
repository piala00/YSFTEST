@echo off
REM Dossier de SIMULATION (donnees fictives) : un mois complet joue par le logiciel, dans un fichier separe
REM (logiciel\simulation.sqlite3). La vraie societe n est jamais touchee. Port 8001.
chcp 65001 >nul
cd /d "%~dp0logiciel"
title ERP OHADA - SIMULATION (donnees fictives)
if not exist .env (
  echo Le logiciel n est pas encore installe : lancez d abord 1-INSTALLER.bat
  pause
  exit /b 1
)
set DB_ENGINE=sqlite
set SQLITE_FICHIER=simulation.sqlite3
set CONTROLE_HEURE_DEPART=0
if not exist simulation.sqlite3 (
  echo.
  echo   Creation du dossier de simulation : septembre 2026, 8 gares, 60 cars, 5 camions, 300 salaries.
  echo   Comptez environ une heure : plus de 50 000 billets joues un par un. Ne fermez pas la fenetre.
  echo.
  "..\python\python.exe" manage.py migrate --noinput || goto erreur
  "..\python\python.exe" manage.py simulation --mois 2026-09 --rapport "%~dp0BILAN-SIMULATION.md" || goto erreur
  echo.
  echo   Choisissez l identifiant et le mot de passe de connexion au dossier de simulation :
  "..\python\python.exe" manage.py createsuperuser || goto erreur
  echo.
  echo   Bilan et controles : BILAN-SIMULATION.md a cote de ce fichier.
)
echo.
echo   SIMULATION demarree sur http://127.0.0.1:8001  (donnees fictives)
echo   Pour l effacer apres l essai : 8-SUPPRIMER-SIMULATION.bat
echo.
start "" cmd /c "timeout /t 4 >nul & start http://127.0.0.1:8001"
"..\python\python.exe" -m waitress --listen=127.0.0.1:8001 --threads=8 erp.wsgi:application
pause
exit /b 0
:erreur
echo.
echo   La simulation a echoue : rien n a ete modifie dans la vraie societe.
echo   Supprimez logiciel\simulation.sqlite3 (8-SUPPRIMER-SIMULATION.bat) puis relancez.
pause
exit /b 1
