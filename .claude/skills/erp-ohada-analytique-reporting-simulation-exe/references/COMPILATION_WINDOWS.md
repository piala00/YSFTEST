# Compiler l'ERP complet pour Windows — contrat de livraison

## Ce qui existe déjà

`desktop/COMPILER.bat` exécute PyInstaller sur cinq scripts en `--onefile` : `commercial.py`, `comptabilite.py`, `analytique.py`, `reporting.py`, `lanceur.py`. `desktop/shell.py` utilise `subprocess.Popen` pour lancer **les quatre EXE voisins**. Si on ne distribue que `ERP_OHADA.exe`, des boutons risquent de ne rien ouvrir. De plus, ces clients utilisent `desktop/api_client.py` pour appeler le serveur. **Compiler le client n'embarque pas automatiquement le serveur Django ni PostgreSQL/SQL Server.**

## Livraison désirée : deux modes, sans promesse impossible

### Mode 1 — Client Windows complet connecté à un serveur ERP

Cible `ERP_OHADA.exe` **unique lanceur de tous les modules** (Commerce, Comptabilité générale, Analytique, Reporting et modules Transport activés). Une fois ouvert, aucun `ERP_Commercial.exe` externe n'est requis pour la navigation, ou alors fournir un installeur/paquet `onedir` qui les contient et les vérifie. L'EXE conserve une configuration de serveur (Render, LAN, serveur local), test de connexion, TLS, utilisateur, droits et messages d'erreur ; l'API Django et la base SQL continuent de fonctionner sur le serveur.

### Mode 2 — Pack Windows autonome avec serveur local (option, si demandée)

Créer un **paquet installable** avec le client, moteur Django, templates/static, migrations, serveur WSGI Windows (ex. Waitress), configuration, schéma de base isolée SQLite pour petite démonstration, logs et sauvegarde. Démarrage/arrêt sécurisé du service local, choix du port, conflit de port, accès localhost et connexion réseau configurée explicitement. SQL Server / PostgreSQL nécessitent un service/base compatible **indépendamment installé ou géré** ; ne prétendez pas intégrer leur serveur complet dans un EXE PyInstaller. Respecter licences et support.

## Stratégie PyInstaller

1. Auditer toutes les dépendances du **client** et éventuels composants du **backend** embarqué. Geler les versions (`requirements-build.txt` ou lock) ; compiler sur Windows (pas de promesse de cross-compilation depuis Linux).
2. Créer un vrai point d'entrée interne (`desktop/lanceur.py` → charge les modules par import/navigation) qui ne dépend plus de `subprocess.Popen` vers des EXE absents en mode fichier unique. Alternative valable : `onedir` avec ses exécutables compagnons, et un installer unique ; signaler le format précisément.
3. Versionner des `.spec` reproductibles, inclure ressources `customtkinter`, icônes, templates, CSS/JS, langues, métadonnées de paquet, cert/CA et fichiers d'initialisation nécessaires. Pour serveur local, inclure modules Django/dynamic imports, migrations, static collectés, gestion des chemins lecture seule vs répertoires utilisateurs en écriture.
4. Emplacements de configuration et données mutables : `%APPDATA%` ou `%LOCALAPPDATA%` de l'utilisateur, pas `sys._MEIPASS` ni sous `Program Files` ; logs avec rotation ; base locale et médias en emplacement sauvegardable. Ne jamais embarquer dans le binaire une clé secrète ou des identifiants de production.
5. BAT `CONSTRUIRE_ERP_COMPLET.bat` (ou script PowerShell) : vérifie prérequis, version Python, installe depuis dépendances verrouillées, exécute tests, nettoie build, construit, calcule SHA256, donne code d'erreur si échec, produit manifeste et dossier `dist`, n'affiche succès qu'après test de démarrage.
6. Tests : Windows 10/11 64 bits vierge, écran connexion, changement serveur, accueil modules, menus/droits, états/export PDF/XLSX, chargement ressources, fichiers temporaires, réseau coupé/reconnecté, mode simulation, fermeture propre ; mode local testé sans Python installé séparément.
7. Lancer et vérifier : pas d'écran blanc ; antivirus éventuel, signature de code si disponible, gestion du contrôle de compte utilisateur (UAC), mise à jour, désinstallation, sauvegarde/rollback, contrat de distribution et version.

## Critères d'acceptation

- En **mode client**, double-clic de `ERP_OHADA.exe` sur Windows sain ; accès effectif à **tous** les modules prévus via le même point d'entrée. Si l'API est distante et absente, afficher « serveur indisponible » et reprise, et **ne pas** prétendre à un fonctionnement hors-ligne.
- En **mode local autonome**, service WSGI et base locale sont installés/démarrés suivant mode documenté, les migrations sont appliquées en test, les données survivent aux redémarrages ; aucune utilisation de `runserver` en production.
- Un `--onefile` compilé mais qui ne contient que le lanceur et exige quatre autres EXE non distribués = **échec**.
- Produire au minimum le ZIP/installeur Windows réellement assemblé et testé, manifeste des dépendances, sommes SHA256, notice d'installation, résultats de tests et limites.

Sources techniques publiques : documentation PyInstaller `https://www.pyinstaller.org/en/stable/usage.html`, `https://pyinstaller.org/en/stable/runtime-information.html` et checklist officielle Django `https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/`. Les arguments et détails doivent être revalidés avec les versions installées au moment de compiler.
