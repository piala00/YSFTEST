@echo off
REM Demarre automatiquement le serveur de l agence a l ouverture de session Windows (ou retire ce demarrage)
chcp 65001 >nul
set "LIEN=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ERP OHADA serveur.bat"
if exist "%LIEN%" (
  del "%LIEN%"
  echo Demarrage automatique du serveur RETIRE.
) else (
  echo @echo off> "%LIEN%"
  echo start "ERP OHADA serveur" /min "%~dp04-DEMARRER-SERVEUR-RESEAU.bat">> "%LIEN%"
  echo Le serveur demarrera automatiquement a chaque ouverture de session Windows sur ce poste.
  echo Relancez ce fichier pour retirer le demarrage automatique.
)
pause
