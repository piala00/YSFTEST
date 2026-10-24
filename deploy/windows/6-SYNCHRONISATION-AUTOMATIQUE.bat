@echo off
REM Transition depuis l ancien logiciel : synchronise automatiquement la copie de son dossier toutes les heures
REM (lecture seule de sa base SQL Server). Relancer ce fichier retire la synchronisation automatique.
chcp 65001 >nul
cd /d "%~dp0"
if not exist logiciel\.env (
  echo Le logiciel n est pas encore installe : lancez d abord 1-INSTALLER.bat
  pause
  exit /b 1
)
schtasks /query /tn "ERP OHADA synchronisation" >nul 2>&1
if not errorlevel 1 (
  schtasks /delete /tn "ERP OHADA synchronisation" /f >nul
  echo Synchronisation automatique RETIREE.
  pause
  exit /b 0
)
findstr /b "SYNCHRO_SERVEUR=" logiciel\.env >nul || (
  echo Indiquez d abord dans logiciel\.env les lignes suivantes, puis relancez ce fichier :
  echo   SYNCHRO_SERVEUR=nom du serveur SQL de l ancien logiciel, ex. .\SQLEXPRESS
  echo   SYNCHRO_BASE=nom de la base du dossier
  echo   SYNCHRO_UTILISATEUR=compte SQL en lecture seule ^(vide : authentification Windows^)
  echo   SYNCHRO_MOT_DE_PASSE=
  echo La premiere synchronisation se fait a l ecran : Fichier ^> Reprise d un dossier existant.
  pause
  exit /b 1
)
> "%~dp0outils\synchroniser.bat" echo @echo off
>> "%~dp0outils\synchroniser.bat" echo cd /d "%~dp0logiciel"
>> "%~dp0outils\synchroniser.bat" echo "..\python\python.exe" manage.py synchroniser_dossier ^> "%~dp0logiciel\derniere-synchronisation.txt" 2^>^&1
schtasks /create /tn "ERP OHADA synchronisation" /sc hourly /tr "\"%~dp0outils\synchroniser.bat\"" /f >nul && (
  echo La copie du dossier d origine sera synchronisee toutes les heures.
  echo Compte rendu du dernier passage : logiciel\derniere-synchronisation.txt
  echo Apres la bascule, la synchronisation ne fait plus rien ; relancez ce fichier pour la retirer.
)
pause
