@echo off
REM ============================================================
REM  Simulateur ERP OHADA Transport  (donnees 100%% fictives)
REM  Dossier PORTABLE : decompressez, puis double-cliquez ce fichier.
REM  Demarre le logiciel en mode simulation (sans licence) et ouvre
REM  directement l atelier de simulation dans le navigateur.
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"
title ERP OHADA - Simulateur (donnees fictives)
set ERP_SIMULATEUR=1
set ERP_DONNEES=%~dp0donnees-simulateur
echo.
echo   Simulateur ERP OHADA Transport (donnees fictives)
echo   Adresse : http://127.0.0.1:8100
echo   Identifiants par defaut : simulateur / simulateur
echo   Gardez cette fenetre ouverte pendant l utilisation ; fermez-la pour arreter.
echo.
"%~dp0ERP-OHADA-Transport.exe"
pause
