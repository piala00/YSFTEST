@echo off
REM Supprime le dossier de SIMULATION (logiciel\simulation.sqlite3). La vraie societe n est pas touchee.
chcp 65001 >nul
cd /d "%~dp0logiciel"
title Supprimer la simulation ERP OHADA
if not exist simulation.sqlite3 (
  echo Aucun dossier de simulation a supprimer.
  pause
  exit /b 0
)
echo.
echo   Le dossier de simulation (donnees fictives) va etre supprime definitivement.
echo   Fermez d abord la fenetre 7-SIMULATION si elle est ouverte.
echo   La vraie societe (db.sqlite3 ou SQL Server) n est pas touchee.
echo.
set /p REPONSE=Tapez OUI pour confirmer : 
if /i not "%REPONSE%"=="OUI" (
  echo Abandon : rien n a ete supprime.
  pause
  exit /b 0
)
del /q simulation.sqlite3 simulation.sqlite3-wal simulation.sqlite3-shm 2>nul
if exist simulation.sqlite3 (
  echo Le fichier est encore utilise : fermez la fenetre 7-SIMULATION et recommencez.
) else (
  echo Dossier de simulation supprime. Pour la vraie societe : 2-DEMARRER-ERP.bat.
)
pause
