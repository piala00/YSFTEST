# Observabilité SQL Server — 28/11/2026

## Base de validation

- Dépôt : `piala00/YSFTEST`.
- Branche de référence : `ccr-5592a371-fusjt2`, SHA `09dc87188bb6d521b86ab65e60970ddc9d612f53`.
- CI complète de référence : run [#747](https://github.com/piala00/YSFTEST/actions/runs/46086942685), conclusion `success`, neuf jobs terminés.
- SQL Server 2022, Django 6.1.3, mssql-django 2.0.0, pilote mssql-python 1.19.0 selon les journaux de recette disponibles.

## Mesures brutes du run #747 sur la branche de référence

| Phase | Shard 0 | Shard 1 |
|---|---:|---:|
| Tests chronométrés | 317 | 505 |
| `setup_databases` | 21,824 s | 15,907 s |
| `run_suite` | 535,184 s | 485,949 s |
| `teardown_databases` | 3,629 s | 3,685 s |
| Connexions ouvertes | 95 | 100 |
| Temps cumulé d'ouverture | 0,320 s | 0,215 s |
| Connexions fermées | 95 | 100 |
| Temps cumulé de fermeture | 0,040 s | 0,030 s |

Tests les plus longs observés :
- Shard 0 : simulation multi-mois 156,459 s ; corrections d'échanges 32,306 s ; miroir de base 27,207 s ; incidents colis 16,362 s.
- Shard 1 : bascule SQLite→SQL Server→SQLite 41,026 s ; contrôle de colonne absente 36,124 s ; scénario trois dossiers 25,389 s ; génération/export/import de dossier 24,503 s.

La simulation multi-mois est le premier coût métier à examiner. Les ouvertures et fermetures de connexion mesurées sont inférieures à une demi-seconde cumulée par shard ; elles n'expliquent pas les durées de plusieurs minutes. Les deux suites terminent sous la limite existante de 16 minutes ; aucun délai n'a été augmenté.

Les blocs `atomic` sont inclusifs et imbriqués. Les durées des opérations sont également imbriquées : `ensure_connection` inclut `connect`, `atomic_scope` inclut les commits/savepoints de son bloc, et `create_test_db` inclut `_create_test_db` puis les migrations. Ne pas additionner ces totaux pour calculer un temps mural. Le classement des tests utilise le plus grand total d'une opération, pas la somme de toutes les opérations. Les transactions de classe `TestCase` enveloppent les transactions de test.

## Instrumentation ajoutée dans ce lot

Le runner conserve les chronométrages existants de chaque test, de son corps, des fixtures, des connexions ouvertes/fermées et des phases du runner. Le dump de pile est armé individuellement pour chaque test ou fixture (180 s par défaut via `SQL_TEST_TRACEBACK_SECONDS`), puis annulé à sa fin ; le timer global périodique de 120 s est supprimé. Il complète ces mesures par :

- `ensure_connection`, `connect`, `close`, `commit`, `rollback`, `set_autocommit` ;
- `savepoint`, `savepoint_commit`, `savepoint_rollback` ;
- `CursorWrapper.execute`, `executemany` et `callproc`, agrégés sans journaliser le SQL ni les paramètres ;
- scopes `transaction.atomic`, profondeur d'imbrication, exceptions et durée inclusive ;
- `create_test_db` et `_create_test_db`, `destroy_test_db` et `_destroy_test_db`, clonage et sérialisation/désérialisation des bases de test.

Les résultats sont agrégés par alias et par test dans `[SQL-DB-SUMMARY]` et `[SQL-DB-TEST-TOP]`. Toute opération dépassant `SQL_DB_SLOW_SECONDS` (5 s par défaut) émet immédiatement `[SQL-DB-SLOW]`, avec opération, alias, durée et test. Aucun SQL, paramètre, montant, nom de client ou donnée métier n'est journalisé. Les marqueurs historiques `[SQL-RESOURCE]` restent également disponibles.

Les durées de `create_test_db` incluent notamment les migrations Django ; `destroy_test_db` inclut la fermeture de connexion. Ces mesures sont des durées globales de méthode, pas un chronométrage isolé de chaque instruction DDL du backend.

## Sources officielles consultées

- Django 6.1.3, `django/db/backends/base/creation.py` : signatures et cycle `create_test_db`, `clone_test_db`, `destroy_test_db` — [source taguée](https://github.com/django/django/blob/6.1.3/django/db/backends/base/creation.py).
- Django 6.1.3, `django/db/backends/utils.py` : `CursorWrapper.execute`, `executemany`, `callproc` — [source taguée](https://github.com/django/django/blob/6.1.3/django/db/backends/utils.py).
- Django 6.1.3, `django/db/transaction.py` : entrée/sortie de `Atomic`, savepoints et rollbacks — [source taguée](https://github.com/django/django/blob/6.1.3/django/db/transaction.py).
- Microsoft mssql-django 2.0.0, `mssql/creation.py` : le backend surcharge `_create_test_db` et `_destroy_test_db`, tandis que les méthodes publiques `create_test_db` et `destroy_test_db` restent héritées — [source taguée](https://github.com/microsoft/mssql-django/blob/2.0.0/mssql/creation.py).

Cette inspection justifie de mesurer les méthodes publiques héritées pour obtenir des durées cohérentes par alias. Le backend surcharge `_destroy_test_db` sans appeler `super()` : pour SQL Server, la durée de destruction est donc garantie par `destroy_test_db`, mais la sous-phase privée n'est pas séparée. Pour la création, le backend appelle `super()._create_test_db()` ; la sous-phase DDL héritée est mesurée distinctement.

## Validation attendue

Le test unitaire `tests.test_sqlserver_runner_partition` couvre l'agrégateur, les alias des connexions et curseurs, la conservation du retour et des paramètres, la propagation des exceptions et la mesure d'une méthode de cycle de vie. Le job SQL Server archive maintenant chaque journal dans `ERP-SQLServer-Diagnostics-0/1` et échoue si `[SQL-DB-SUMMARY]` ou `[SQL-DB-TEST-TOP]` manque. La CI complète doit montrer les nouveaux marqueurs `[SQL-DB-SUMMARY]`, `[SQL-DB-TEST-TOP]` et `[SQL-DB-SLOW]` dans les deux shards SQL Server.

La limite GNU `timeout ... 16m` reste inchangée. Aucun timeout n'est allongé ; aucune fusion, aucun déploiement et aucune donnée réelle ne sont autorisés.
