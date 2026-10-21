@echo off
REM Compile les logiciels ERP OHADA en executables Windows (dossier dist\)
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ERP_Commercial --collect-all customtkinter commercial.py
pyinstaller --noconfirm --onefile --windowed --name ERP_Comptabilite --collect-all customtkinter comptabilite.py
pyinstaller --noconfirm --onefile --windowed --name ERP_Reporting --collect-all customtkinter reporting.py
pyinstaller --noconfirm --onefile --windowed --name ERP_OHADA --collect-all customtkinter lanceur.py
echo.
echo Executables disponibles dans le dossier dist\
pause
