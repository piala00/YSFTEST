@echo off
REM Dossier de SIMULATION (donnees fictives) : les mois choisis (jusqu a aujourd hui si on le demande), joues par le logiciel, dans un fichier separe
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
set DEBUT=2026-09
set DUREE=A
if exist simulation.sqlite3 goto demarrer
set /p DEBUT=Premier mois a simuler, AAAA-MM (ex. 2026-01) [2026-09] : 
if "%DEBUT%"=="" set DEBUT=2026-09
echo   Duree : A = jusqu a aujourd hui, ou un nombre de mois (1 a 24).
set /p DUREE=Duree [A] : 
if "%DUREE%"=="" set DUREE=A
if /i "%DUREE%"=="A" (set "PERIODE=--jusqu-au aujourdhui") else (set "PERIODE=--nombre-mois %DUREE%")
echo.
echo   Creation du dossier de simulation a partir de %DEBUT% (duree : %DUREE%) : 8 agences, 60 cars, 5 camions, 300 salaries.
echo   Comptez environ une heure par mois : plus de 50 000 billets par mois joues un par un. Ne fermez pas la fenetre.
echo.
"..\python\python.exe" manage.py migrate --noinput || goto erreur
"..\python\python.exe" manage.py simulation --mois %DEBUT% %PERIODE% --rapport "%~dp0BILAN-SIMULATION.md" || goto erreur
echo.
echo   Choisissez l identifiant et le mot de passe de connexion au dossier de simulation :
"..\python\python.exe" manage.py createsuperuser || goto erreur
echo.
echo   Bilan et controles : BILAN-SIMULATION.md a cote de ce fichier.
:demarrer
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
