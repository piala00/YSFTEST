@echo off
REM Choisir une autre base (SQLite ou SQL Server). L ancienne base n est pas effacee.
chcp 65001 >nul
cd /d "%~dp0"
title Changer de base ERP OHADA
"python\python.exe" outils\installer.py changer-base
