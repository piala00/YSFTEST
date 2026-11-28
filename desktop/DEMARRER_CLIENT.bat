@echo off
REM Lance le portail des logiciels ERP OHADA
cd /d "%~dp0"
if not exist .venv (
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)
start "" pythonw lanceur.py
