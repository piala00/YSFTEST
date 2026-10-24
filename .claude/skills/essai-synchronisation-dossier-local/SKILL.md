---
name: essai-synchronisation-dossier-local
description: Conduire, sur le PC de l'utilisateur, un essai de synchronisation d'un dossier Sage 100 SQL Server réel vers une base ERP d'essai séparée (par défaut : reports à nouveau et données de janvier), en lecture seule. Utiliser quand l'utilisateur demande de connecter l'ERP à sa base Sage, de tester la reprise ou la synchronisation sur ses données, ou de « faire l'essai de janvier ».
---

# Essai de synchronisation sur le PC de l'utilisateur

Tu travailles dans le dossier `ERP-OHADA\logiciel` installé par `1-INSTALLER.bat`, sur l'ordinateur de l'utilisateur, avec ses
**données réelles**. Le Python de l'ERP est `..\python\python.exe`. Les commandes ci-dessous sont écrites pour PowerShell.

## Règles absolues

1. **Sage en lecture seule.** Ne passe que par `manage.py reprise_sage` (SELECT seulement, connexion `ApplicationIntent=ReadOnly`,
   toute autre instruction est refusée par le code). N'exécute jamais `sqlcmd`, `Invoke-Sqlcmd`, SSMS ni aucun script qui écrit,
   crée, modifie, sauvegarde, restaure ou détache quoi que ce soit sur le serveur SQL de Sage. Ne modifie pas le service SQL Server.
2. **Base ERP d'essai séparée.** Avant toute commande `manage.py`, fixe `$env:SQLITE_FICHIER = "essai-janvier.sqlite3"` dans le
   même terminal (variable vérifiée à chaque commande). Ne touche jamais `db.sqlite3` ni la base ERP de production, et ne donne
   jamais le nom d'une base Sage comme base de l'ERP.
3. **C'est l'utilisateur qui désigne** le serveur, l'instance et la base Sage de l'essai, ainsi que le début de l'exercice. Ne
   choisis pas à sa place ; en cas de doute, demande.
4. **Mot de passe SQL.** Préfère l'authentification Windows (pas d'`--utilisateur`). Avec un compte SQL, demande à l'utilisateur
   d'écrire lui-même `SYNCHRO_MOT_DE_PASSE=...` dans `logiciel\.env` ; ne lui demande pas de le coller dans la conversation, ne
   l'affiche pas, ne l'écris pas dans un autre fichier.
5. **Données réelles = confidentielles.** Ne fais ni `git add`, ni commit, ni push depuis ce PC ; ne copie aucune donnée (rapport,
   base d'essai, extrait) dans le dépôt, sur Internet ou dans un ticket. Résume les rapports (contrôles, nombres, anomalies par
   type) plutôt que de recopier des listes de clients ou de montants. Les rapports restent dans `logiciel\` (fichiers
   `rapport-*.txt`, ignorés par git).
6. **Stop sur anomalie.** Si un contrôle est en écart, ou si une commande renvoie une erreur inattendue, arrête-toi, explique, et
   ne relance pas avec `--appliquer`. N'essaie pas de « corriger » le dossier Sage.

## Étapes

```powershell
cd <dossier>\ERP-OHADA\logiciel
$env:SQLITE_FICHIER = "essai-janvier.sqlite3"
$py = "..\python\python.exe"
```

1. **Repérer instances et bases** (l'utilisateur choisit ensuite) :
   `& $py manage.py reprise_sage --lister --serveur localhost` (ajouter `--instance NOM` pour une instance nommée, `--utilisateur`
   pour un compte SQL). Si aucune instance n'est détectée : service « SQL Server Browser » arrêté ; demander le nom de l'instance.
2. **Créer la base ERP d'essai** (vide, sans démonstration) :
   `& $py manage.py migrate` puis `& $py manage.py init_erp --admin <mot de passe choisi par l'utilisateur>`.
   L'exercice créé est celui de l'année en cours : les données de janvier doivent appartenir à cet exercice (sinon, le signaler).
3. **Simulation, reports et janvier** (rien n'est enregistré) :
   ```powershell
   & $py manage.py reprise_sage --serveur <ORDINATEUR> --instance <INSTANCE> --base <BASE> `
       --debut-exercice <AAAA-01-01 ou début réel> --date-bascule <AAAA-01-31> --historique-depuis <AAAA-01-01> `
       --rapport rapport-janvier-simulation.txt
   ```
   - Écritures : du début d'exercice au 31/01, **reports à nouveau compris** (journal d'à-nouveaux), ligne à ligne, avec lettrage.
   - Pièces commerciales : celles de janvier, plus **toutes** les pièces encore en cours et factures non soldées *aujourd'hui*.
   - Stock : le stock **actuel** du dossier (F_ARTSTOCK n'a pas d'historique) — pas celui du 31/01 ; c'est attendu pour l'essai.
4. **Lire le rapport avec l'utilisateur.** Contrôles `[OK]` / `[ÉCART]`, puis rapprochement dans Sage par l'utilisateur :
   balance générale du début d'exercice au 31/01 (totaux débit / crédit = contrôles « Écritures » du rapport), balance des tiers,
   total TTC des factures. Noter les anomalies non bloquantes.
5. **Synchroniser pour de bon** si tout est conforme et que l'utilisateur le confirme : même commande avec `--appliquer` et
   `--rapport rapport-janvier-synchronisation.txt`. La base d'essai passe en « copie synchronisée ».
6. **Vérifier l'incrémental** : relancer la même commande avec `--appliquer` : le rapport doit indiquer 0 créée / 0 mise à jour
   (sauf saisies faites entre-temps dans Sage). Pour aller plus loin : `--date-bascule` au 28/02, seuls les ajouts de février
   doivent apparaître.
7. **Consulter dans l'ERP** (base d'essai, port 8001 pour ne pas gêner l'ERP habituel) :
   `& $py -m waitress --listen=127.0.0.1:8001 erp.wsgi:application`, puis http://127.0.0.1:8001 (compte `admin`) : plan
   comptable, tiers, journaux, écritures de janvier, balance, pièces, Fichier › Reprise d'un dossier existant (derniers passages).
8. **Compte rendu** à l'utilisateur : contrôles, volumes, anomalies par type, écarts constatés avec Sage, durée. Ne pas faire la
   bascule (`BASCULER`) pendant un essai.

Pour recommencer à zéro : arrêter le serveur d'essai, supprimer `essai-janvier.sqlite3` (et ses fichiers `-wal` / `-shm`), reprendre
à l'étape 2. Ne supprimer aucun autre fichier.
