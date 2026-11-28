# 06 — Compilation du logiciel entier pour Windows

**Constat de l'archive source** : `desktop/COMPILER.bat` compile déjà cinq clients CustomTkinter (Commercial, Comptabilité générale, Analytique, Reporting, lanceur) mais **pas le serveur Django**. Par ailleurs, `deploy/windows/construire_paquet.sh` empaquette le code avec un environnement Python, ce qui n'est pas l'équivalent d'un serveur compilé.

## Amélioration ajoutée dans les sources proposées
- `logiciel/packaging/windows/COMPILER-ERP-COMPLET.bat` prépare dépendances, contrôle Django, collecte les statiques, puis construit les clients **et le serveur** `ERP_Transport_Serveur.exe` via PyInstaller `--onedir`.
- `logiciel/packaging/windows/serveur_local.py` sert le WSGI Django via Waitress, charge un `.env` situé **à côté de l'exécutable**, persiste la base SQLite dans `donnees` (ou passe à une base distante configurée), propose une initialisation EXPLICITE des migrations et la création interactive du compte administrateur. Sa disponibilité réseau est limitée à localhost par défaut.
- `9-COMPILER-ERP-COMPLET.bat` ajoute l'option de compilation au paquet de lancement Windows.

## Distinction fondamentale
Un `.exe` emballant Django + le client ne contient **pas** forcément SQL Server, PostgreSQL, les bases de données, les données partagées, les sauvegardes, la synchronisation, les certificats ou les secrets. La forme fiable à tester en premier est un **paquet Windows composé d'un exécutable serveur et de plusieurs exécutables bureau**, éventuellement distribué via un installateur signé. L'objectif d'un unique `.exe` autonome est une variante à valider, pas une promesse.

## Procédure et tests bloquants
1. Tester sur Windows 10/11, architecture x64, même version de Python que sur le serveur cible ; valider avec un compte non administrateur.
2. Installer dépendances proprement et construire dans un environnement de build séparé ; installer PyInstaller localement dans ce venv.
3. Inclure modules Django dynamiques, migrations, templates, `staticfiles`, fichiers de package et ressources CustomTkinter ; ne jamais intégrer secrets, `db.sqlite3` ou données de production.
4. Vérifier `ERP_Transport_Serveur.exe --version`, puis `--initialiser-base` sur une base de DEMONSTRATION autorisée ; lancement localhost, connexion bureau, modules, factures, impressions, rapports, états et droits.
5. Vérifier utilisateur au guichet hors réseau siège ; gestion de services Windows/arrêt propre ; restauration de DB, migration de version, pare-feu et TLS/VPN pour accès distant.
6. Examiner antivirus, signature de code, dépendances VC et logs, vérifier Windows Defender. Une compilation réussie ne prouve pas que le programme démarre ni fonctionne correctement.

## Références officielles
- https://pyinstaller.org/en/stable/ (PyInstaller n'est pas cross-compiler : construire Windows sous Windows).
- https://nuitka.net/user-documentation/user-manual.html (solution alternative, standalone/onefile et contraintes de C compiler).
- https://docs.djangoproject.com/en/stable/howto/deployment/checklist/ (audit de sécurité et déploiement).

## Commerce et Transport
Le paquet Windows actuel peut être décliné en deux éditions et utilise des paramétrages de société/activité distincts, mais les binaires et installations doivent être isolés ou configurés pour chaque dossier ; ne jamais fusionner bases commerciales et transport sans plan explicite.
