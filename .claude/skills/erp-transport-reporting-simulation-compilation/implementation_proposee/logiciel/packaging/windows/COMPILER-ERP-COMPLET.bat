@echo off
setlocal EnableExtensions
chcp 65001 >nul
REM À exécuter sur Windows dans le dossier logiciel\packaging\windows\
cd /d "%~dp0\..\.."
echo ==============================================
echo ERP Transport - Compilation Windows (serveur + bureau)
echo ==============================================
where py >nul 2>&1
if errorlevel 1 (
  echo Python pour Windows est requis, avec son lanceur py.exe.
  exit /b 1
)
if not exist ".venv-build\Scripts\python.exe" py -3 -m venv ".venv-build"
if errorlevel 1 exit /b 1
set "PY=.venv-build\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"%PY%" -m pip install -r requirements.txt -r desktop\requirements.txt waitress pyinstaller
if errorlevel 1 exit /b 1
"%PY%" manage.py check
if errorlevel 1 exit /b 1
"%PY%" manage.py collectstatic --noinput
if errorlevel 1 exit /b 1
if not exist packaging\windows\sortie mkdir packaging\windows\sortie
REM Le serveur ERP est un exécutable distinct des clients bureau.
"%PY%" -m PyInstaller --noconfirm --clean --onedir --console --name ERP_Transport_Serveur ^
 --distpath packaging\windows\sortie --workpath packaging\windows\temp_build ^
 --collect-submodules apps --collect-submodules erp --collect-all django ^
 --add-data "templates;templates" --add-data "staticfiles;staticfiles" ^
 packaging\windows\serveur_local.py
if errorlevel 1 exit /b 1
for %%E in (lanceur commercial comptabilite analytique reporting) do (
  "%PY%" -m PyInstaller --noconfirm --clean --onedir --windowed --name ERP_%%E ^
    --distpath packaging\windows\sortie --workpath packaging\windows\temp_build ^
    --paths desktop --collect-all customtkinter desktop\%%E.py
  if errorlevel 1 exit /b 1
)
copy /Y "packaging\windows\.env.exemple" "packaging\windows\sortie\ERP_Transport_Serveur\.env.exemple" >nul
copy /Y "packaging\windows\README_COMPILATION.md" "packaging\windows\sortie\LISEZ_MOI.md" >nul
echo.
echo Compilation terminee. Les programmes se trouvent sous packaging\windows\sortie\
echo IMPORTANT : un .exe ne remplace pas la base de donnees ni les sauvegardes.
exit /b 0
