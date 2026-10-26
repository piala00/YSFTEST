# Procédure d'intégration contrôlée (pour Claude Code)

## 1. Déterminer le répertoire racine

Dans l'archive d'origine, le projet Django se trouve sous :
`ERP-OHADA-Commerce/logiciel/` (présence de `manage.py`, `apps/`, `desktop/`).

La commande de patch s'exécute **depuis `logiciel/`**, pas depuis le dossier supérieur `ERP-OHADA-Commerce/`.

## 2. Auditer la version réelle

- Identifier l'état du dépôt, la branche, les changements non enregistrés et les migrations de base.
- Si le code a évolué depuis l'archive, utiliser les règles métier et le patch comme **référence de comparaison**, pas comme un fichier à imposer par écrasement.
- Ne pas ajouter de secrets, ni modifier `.env` ou la base réelle.

## 3. Prévisualiser le patch (optionnel)

Sur une copie propre de la version *origine* fournie en octobre 2026 :

```bash
cd ERP-OHADA-Commerce/logiciel
git apply --check /chemin/vers/references/PATCH_CODE_COMMERCE.patch
```

**Si cette vérification échoue**, NE PAS appliquer le patch aveuglément : relire le diff et réconcilier les fichiers avec les changements du dépôt actuel.

Si elle réussit et après sauvegarde/validation du code source, appliquer :

```bash
git apply /chemin/vers/references/PATCH_CODE_COMMERCE.patch
```

Le patch ne contient ni projet Django complet ni base de données. Une note technique figure dans `NOTE_CORRECTIF_ORIGINAL.txt` et peut être incorporée au dépôt si souhaité.

## 4. Nouvelles sociétés

Le code de référence `apps/core/management/commands/init_erp.py` possède déjà le défaut `--longueur-comptes 7`.
Vérifier que les nouvelles sociétés créées par **tous** les parcours (web, bureau, admin, CLI, import) sont initialisées de façon cohérente ; ne pas supposer que la valeur de champ en base `0` a changé globalement.

## 5. Sociétés avec plan existant

1. Réaliser une **sauvegarde testée** (export/restauration de la base). Noter les nombres de comptes et d'écritures, balances, lettrages et soldes.
2. Vérifier l'absence de synchronisation en cours, particulièrement Sage en `SYNCHRO_MIROIR`.
3. Sur une copie de base non productive, exécuter :
   ```bash
   python manage.py longueur_comptes --longueur 7
   ```
4. Vérifier comptes non numériques, > 7 chiffres et doublons de destination. En cas de conflit, faire arbitrer les numéros par le responsable comptable ; **aucune fusion automatique**.
5. Après accord explicite et dans une fenêtre de maintenance, sur l'environnement choisi :
   ```bash
   python manage.py longueur_comptes --longueur 7 --appliquer
   ```
6. Contrôler l'exactitude de `Societe.longueur_comptes`, le format des comptes, la réconciliation des journaux/écritures, le lettrage, les pièces, les états, et les flux applicatifs.
7. Retour arrière : restaurer la sauvegarde si une incohérence majeure est constatée. Ne pas promettre une opération inverse triviale.

## 6. Tests et déploiement

```bash
python manage.py check
python manage.py test apps.comptabilite apps.transport
```

Adapter à la configuration réelle du projet. À la fin, décrire précisément les tests lancés (environnement, réussite/échec, limitations), puis **demander l'accord avant tout déploiement en production**.

Pour le client Windows, compiler via `desktop/COMPILER.bat` sur Windows avec l'environnement et PyInstaller requis. Vérifier que `ERP_Analytique.exe` est généré, lancé et raccordé au même serveur que la comptabilité générale.

## 7. Droits et sécurité

- Deux entrées au portail doivent respecter le profil et les autorisations existantes.
- Un accès direct à une URL ou API analytique non autorisée doit être bloqué côté serveur.
- Aucun nouvel utilisateur, mot de passe ou compte de production n'est nécessaire pour ce correctif.
