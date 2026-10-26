@echo off
chcp 65001 >nul
if not exist "%~dp0logiciel\packaging\windows\COMPILER-ERP-COMPLET.bat" (
 echo Option de compilation absente. Verifier le dossier logiciel.
 pause
 exit /b 1
)
call "%~dp0logiciel\packaging\windows\COMPILER-ERP-COMPLET.bat"
if errorlevel 1 (
 echo La compilation a echoue. Consultez les messages ci-dessus.
 pause
 exit /b 1
)
echo Compilation terminee : voir logiciel\packaging\windows\sortie
pause
