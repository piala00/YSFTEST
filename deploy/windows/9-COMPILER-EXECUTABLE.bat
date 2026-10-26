@echo off
REM Compile TOUT le logiciel en un programme Windows, sans Internet :
REM   executable\ERP-OHADA-<Edition>\ERP-OHADA-<Edition>.exe  (le dossier entier se copie sur un autre PC)
REM Lancez d abord 1-INSTALLER.bat une fois.
chcp 65001 >nul
cd /d "%~dp0logiciel"
title Compilation ERP OHADA
set /p ERP_EDITION=<"%~dp0outils\edition.txt"
echo.
echo   Compilation de l ERP %ERP_EDITION% en programme Windows : quelques minutes.
echo.
"..\python\python.exe" -m pip install --no-index --find-links "..\paquets" --disable-pip-version-check -q -r "..\outils\composants.txt" -r "..\outils\compilation.txt" || goto erreur
"..\python\python.exe" manage.py collectstatic --noinput -v0 || goto erreur
"..\python\python.exe" -m PyInstaller deploy\executable\erp_ohada.spec --noconfirm --workpath "%~dp0compilation" --distpath "%~dp0executable" || goto erreur
echo.
echo   Programme pret : executable\ERP-OHADA-%ERP_EDITION%\ERP-OHADA-%ERP_EDITION%.exe
echo   Copiez tout le dossier ERP-OHADA-%ERP_EDITION% sur le poste voulu, puis double-cliquez sur le .exe.
echo   Ses donnees seront dans le sous-dossier donnees, a cote du programme.
pause
exit /b 0
:erreur
echo.
echo   La compilation a echoue : lisez le message ci-dessus. Le logiciel installe n est pas modifie.
pause
exit /b 1
