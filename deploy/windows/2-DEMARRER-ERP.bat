@echo off
REM Demarre l ERP sur ce poste et ouvre le navigateur. Fermer cette fenetre arrete le logiciel.
chcp 65001 >nul
cd /d "%~dp0logiciel"
title ERP OHADA - ne pas fermer pendant l utilisation
if not exist .env (
  echo Le logiciel n est pas encore installe : lancez d abord 1-INSTALLER.bat
  pause
  exit /b 1
)
echo.
echo   ERP OHADA demarre sur http://127.0.0.1:8000
echo   Gardez cette fenetre ouverte pendant l utilisation ; fermez-la pour arreter le logiciel.
echo.
start "" cmd /c "timeout /t 4 >/dev/null & start http://127.0.0.1:8000"
"..\python\python.exe" -m waitress --listen=127.0.0.1:8000 --threads=8 erp.wsgi:application
pause
