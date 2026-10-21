@echo off
REM Compile le client bureau en executable Windows (dist\ERP_OHADA.exe)
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ERP_OHADA --collect-all customtkinter app.py
pause
