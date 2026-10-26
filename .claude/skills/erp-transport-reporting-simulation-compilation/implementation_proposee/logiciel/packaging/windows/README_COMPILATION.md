# Compiler l'ERP Transport sur Windows — guide de déploiement

Ce dossier ajoute **une option de compilation**, et non un `.exe` déjà compilé.
Compiler uniquement sur un poste Windows compatible avec les dépendances installées.

1. Installer Python et son lanceur `py` sur Windows. Effectuer une sauvegarde et préparer une **base de TEST**, jamais la base de production.
2. Dans l'Explorateur Windows, lancer `COMPILER-ERP-COMPLET.bat` depuis `logiciel/packaging/windows/`.
3. Il construit les applications de bureau (`ERP_lanceur.exe`, etc.) **et le serveur** (`ERP_Transport_Serveur.exe`) dans `packaging/windows/sortie`.
4. Copier `.env.exemple` en `.env` à côté de l'exécutable serveur ; choisir une nouvelle `SECRET_KEY`, configurer les hôtes, le moteur et le chemin de la base **hors de l'exécutable**.
5. Pour un dossier neuf, lancer EXPLICITEMENT `ERP_Transport_Serveur.exe --initialiser-base`, puis démarrer normalement.
6. Vérifier en poste Windows vierge : connexion au serveur local, UI, fichiers statiques, modules généraux/analytique, permissions, impression, synchronisation et restaurations.

## Architecture recommandée

- **Un serveur d'agence** avec une base PostgreSQL/SQL Server (ou SQLite pour un essai mono-poste uniquement) et l'exécutable serveur.
- **Des clients bureau Windows** sur le réseau local, chacun avec son exécutable. Les clients ont besoin du serveur et de la base : les empaqueter en `.exe` ne les rend pas autonomes.
- Si le siège est hors ligne, l'agence doit garder son serveur local. Le mécanisme de synchronisation n'est pas automatiquement résolu par le packaging.
- Ne pas exposer Waitress directement sur Internet : configurer un frontal sécurisé ou un VPN, TLS, contrôle des accès et pare-feu.
- Distribuer de préférence les dossiers `--onedir` ou un installeur signé ; `--onefile` peut compliquer le démarrage du serveur et l'accès aux fichiers.
- L'archive source n'inclut ni secrets de production ni base de production ; ne pas les incorporer lors de la compilation.

## Tests bloquants

- Le serveur démarre sans créer une DB nouvelle à la place d'une DB de production existante.
- Les migrations ne s'exécutent pas silencieusement lors de chaque démarrage.
- Les fichiers statiques, templates, Django migrations et bibliothèques incluses sont présents.
- Les droits comptables, imprimantes, rapports PDF, 10 plans analytiques et comparateurs sont testés.
- Les journaux comptables conservent débit = crédit et les écritures analytiques ont leurs références générales.
- Le binaire ne dépend pas de Python installé sur le poste cible et ne contient aucun `.env` secret.
- Sauvegarde/restauration, mise à jour et retour arrière documentés avant toute livraison.

**Limite** : ce script est une base de construction adaptée au projet inspecté. Les binaires doivent encore être construits et qualifiés sur Windows avant mise en production.

Après les migrations et avant le premier accès, `ERP_Transport_Serveur.exe --creer-admin` permet de créer le compte administrateur de façon interactive, sans mot de passe inscrit dans un script.
