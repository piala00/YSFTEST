@echo off
REM Demarre le serveur ERP (premier lancement : installe et initialise)
cd /d "%~dp0"
if not exist .venv (
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py init_erp --admin admin123
) else (
    call .venv\Scripts\activate.bat
)
python manage.py runserver 0.0.0.0:8000
pause
