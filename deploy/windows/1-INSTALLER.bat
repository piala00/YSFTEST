@echo off
REM Installation de l ERP (premiere fois, ou pour reparer) : aucune connexion Internet necessaire
chcp 65001 >nul
cd /d "%~dp0"
title Installation ERP OHADA
"python\python.exe" outils\installer.py
