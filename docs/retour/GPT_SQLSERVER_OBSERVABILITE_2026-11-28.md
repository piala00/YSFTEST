# Observabilité SQL Server — 28/11/2026

## Base de validation

- Dépôt : `piala00/YSFTEST`.
- Base applicative : branche candidate `gpt/analytique-service-paie-20261128`, elle-même issue de `ccr-5592a371-fusjt2`.
- CI complète de référence : run [#763](https://github.com/piala00/YSFTEST/actions/runs/46097718301), conclusion `success`, neuf jobs terminés.
- SQL Server 2022, Django 6.1.3, mssql-django 2.0.0, pilote mssql-python 1.19.0 selon les journaux de cette recette.

## Mesures brutes du run #763

| Phase | Shard 0 | Shard 1 |
|---|---:|---:|
| Tests chronométrés | 327 | 496 |
| `run_suite` | 397,405 s | 499,996 s |
| `setup_databases` | 16,827 s | 17,512 s |
| `teardown_databases` | 3,632 s | 3,915 s |
| Connexions ouvertes | 95 | 100 |
| Temps cumulé d'ouverture | 0,252 s | 0,230 s |
| Connexions fermées | 95 | 100 |
| Temps cumulé de fermeture | 0,031 s | 0,031 s |

Tests les plus longs observés :
- Shard 0 : bascule SQLite→SQL Server→SQLite 42,037 s ; contrôle de colonne absente 38,964 s ; scénario trois dossiers 26,778 s ; génération/export/import de dossier 24,785 s.
- Shard 1 : simulation multi-mois 115,600 s ; synchronisation par relais 22,743 s ; changement de moteur 20,592 s ; imprévus de voyage 15,559 s.

La simulation multi-mois est le premier coût métier à examiner. Les ouvertures et fermetures de connexion mesurées sont inférieures à une seconde cumulée par shard ; elles n'expliquent pas les durées de plusieurs minutes.

Les blocs `atomic` sont inclusifs et imbriqués : ne pas additionner leurs durées pour calculer un temps mural. Les transactions de classe `TestCase` enveloppent les transactions de test.

## Instrumentation ajoutée dans ce lot

Le runner conserve les chronométrages existants de chaque test, de son corps, des fixtures, des connexions ouvertes/fermées et des phases du runner. Il complète ces mesures par :

- `ensure_connection`, `connect`, `close`, `commit`, `rollback`, `set_autocommit` ;
- `savepoint`, `savepoint_commit`, `savepoint_rollback` ;
- scopes `transaction.atomic`, profondeur d'imbrication, exceptions et durée inclusive ;
- `create_test_db` et `_create_test_db`, `destroy_test_db` et `_destroy_test_db`, `clone_test_db` et `_clone_test_db`, sérialisation et désérialisation des bases de test. Les méthodes internes de création sont mesurées lorsqu'elles sont héritées/appelées par le backend ; la méthode publique mesure toujours le cycle complet.

Les résultats sont agrégés par alias et par test dans `[SQL-DB-SUMMARY]` et `[SQL-DB-TEST-TOP]`. Aucun SQL, paramètre, montant, nom de client ou donnée métier n'est journalisé. Les wrappers conservent les retours et propagent les exceptions originales.

Les durées de `create_test_db` incluent notamment les migrations Django ; `destroy_test_db` inclut la fermeture de connexion. Ces mesures sont des durées globales de méthode, pas un chronométrage isolé de chaque instruction DDL du backend.

## Sources officielles consultées

- Django 6.1.3, `django/db/backends/base/creation.py` : signatures et cycle `create_test_db`, `clone_test_db`, `destroy_test_db` — [source taguée](https://github.com/django/django/blob/6.1.3/django/db/backends/base/creation.py).
- Django 6.1.3, `django/db/transaction.py` : entrée/sortie de `Atomic`, savepoints et rollbacks — [source taguée](https://github.com/django/django/blob/6.1.3/django/db/transaction.py).
- Microsoft mssql-django 2.0.0, `mssql/creation.py` : le backend surcharge `_create_test_db` et `_destroy_test_db`, tandis que les méthodes publiques `create_test_db` et `destroy_test_db` restent héritées — [source taguée](https://github.com/microsoft/mssql-django/blob/2.0.0/mssql/creation.py).

Cette inspection justifie de mesurer les méthodes publiques héritées pour obtenir des durées cohérentes par alias, sans supposer que les méthodes internes du backend SQL Server sont celles de Django. Le backend surcharge `_destroy_test_db` sans appeler `super()` : pour SQL Server, la durée de destruction est donc garantie par `destroy_test_db`, mais la sous-phase privée n'est pas séparée. Pour la création, le backend appelle `super()._create_test_db()` ; la sous-phase DDL héritée est donc mesurée distinctement.

## Validation attendue

Le test unitaire `tests.test_sqlserver_runner_partition` couvre l'agrégateur, les alias, la conservation du retour, la propagation des exceptions et la mesure d'une méthode de cycle de vie. La CI complète doit ensuite montrer les nouveaux marqueurs `[SQL-DB-SUMMARY]` et `[SQL-DB-TEST-TOP]` dans les deux shards SQL Server.

La limite GNU `timeout ... 16m` reste inchangée. Aucun timeout n'est allongé ; aucune fusion, aucun déploiement et aucune donnée réelle ne sont autorisés.
