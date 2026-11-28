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

Les durées des opérations sont imbriquées : `ensure_connection` inclut `connect`, `atomic_scope` inclut les commits/savepoints de son bloc, et `create_test_db` inclut `_create_test_db` puis les migrations. Ne pas additionner ces totaux pour calculer un temps mural. Le classement des tests utilise le plus grand total d'une opération, pas la somme de toutes les opérations. Les transactions de classe `TestCase` enveloppent les transactions de test.

## Instrumentation ajoutée dans ce lot

Le runner conserve les chronométrages existants de chaque test, de son corps, des fixtures, des connexions ouvertes/fermées et des phases du runner. Il complète ces mesures par :

- `ensure_connection`, `connect`, `close`, `commit`, `rollback`, `set_autocommit` ;
- `CursorWrapper.execute`, `executemany` et `callproc`, agrégés sans journaliser le SQL ni les paramètres ;
- `savepoint`, `savepoint_commit`, `savepoint_rollback` ;
- scopes `transaction.atomic`, profondeur d'imbrication, exceptions et durée inclusive ;
- `create_test_db` et `_create_test_db`, `destroy_test_db` et `_destroy_test_db`, `clone_test_db` et `_clone_test_db`, sérialisation et désérialisation des bases de test. Les méthodes internes de création sont mesurées lorsqu'elles sont héritées/appelées par le backend ; la méthode publique mesure toujours le cycle complet.

Les résultats sont agrégés par alias et par test dans `[SQL-DB-SUMMARY]` et `[SQL-DB-TEST-TOP]`. Toute opération dépassant `SQL_DB_SLOW_SECONDS` (5 s par défaut) émet immédiatement `[SQL-DB-SLOW]`, avec opération, alias, durée et test, sans SQL ni paramètre. Aucun montant, nom de client ou donnée métier n'est journalisé. Les marqueurs historiques `[SQL-RESOURCE]` restent également disponibles. Les wrappers conservent les retours et propagent les exceptions originales.

Les durées de `create_test_db` incluent notamment les migrations Django ; `destroy_test_db` inclut la fermeture de connexion. Ces mesures sont des durées globales de méthode, pas un chronométrage isolé de chaque instruction DDL du backend.

## Sources officielles consultées

- Django 6.1.3, `django/db/backends/base/creation.py` : signatures et cycle `create_test_db`, `clone_test_db`, `destroy_test_db` — [source taguée](https://github.com/django/django/blob/6.1.3/django/db/backends/base/creation.py).
- Django 6.1.3, `django/db/transaction.py` : entrée/sortie de `Atomic`, savepoints et rollbacks — [source taguée](https://github.com/django/django/blob/6.1.3/django/db/transaction.py).
- Microsoft mssql-django 2.0.0, `mssql/creation.py` : le backend surcharge `_create_test_db` et `_destroy_test_db`, tandis que les méthodes publiques `create_test_db` et `destroy_test_db` restent héritées — [source taguée](https://github.com/microsoft/mssql-django/blob/2.0.0/mssql/creation.py).

Cette inspection justifie de mesurer les méthodes publiques héritées pour obtenir des durées cohérentes par alias, sans supposer que les méthodes internes du backend SQL Server sont celles de Django. Le backend surcharge `_destroy_test_db` sans appeler `super()` : pour SQL Server, la durée de destruction est donc garantie par `destroy_test_db`, mais la sous-phase privée n'est pas séparée. Pour la création, le backend appelle `super()._create_test_db()` ; la sous-phase DDL héritée est donc mesurée distinctement.

## Validation attendue

Le test unitaire `tests.test_sqlserver_runner_partition` couvre l'agrégateur, les alias des connexions et curseurs, la conservation du retour et des paramètres, la propagation des exceptions et la mesure d'une méthode de cycle de vie. La CI complète doit ensuite montrer les nouveaux marqueurs `[SQL-DB-SUMMARY]` et `[SQL-DB-TEST-TOP]` dans les deux shards SQL Server.

La limite GNU `timeout ... 16m` reste inchangée. Aucun timeout n'est allongé ; aucune fusion, aucun déploiement et aucune donnée réelle ne sont autorisés.


## Relecture complémentaire des journaux CI #797 — 28/11/2026

Le run [#797](https://github.com/piala00/YSFTEST/actions/runs/46103205466) a terminé avec **9 jobs sur 9 en succès**. Les deux shards SQL Server 2022 ont terminé sous le timeout inchangé de 16 minutes :

| Mesure observée | Shard 0 | Shard 1 |
|---|---:|---:|
| Tests exécutés | 317 | 505 |
| Durée de suite | 542,524 s | 522,821 s |
| Création de la base de test | 21,458 s | 18,323 s |
| Destruction de la base | 3,595 s | 3,866 s |
| Connexions ouvertes (durée cumulée) | 0,262 s | 0,210 s |
| Connexions fermées (durée cumulée) | 0,039 s | 0,033 s |

Les journaux confirment que les connexions ne sont pas le coût dominant. La simulation multi-mois et les fixtures de classe restent les principaux consommateurs de temps. Les requêtes lentes sont identifiables par durée, alias et test, sans SQL ni paramètres journalisés.

La même CI confirme la suite SQLite (**822 tests**, 205,127 s, 18 ignorés) et la recette P0.3 sur deux bases Django réellement migrées (**14 tests**, 65,358 s). Les deux jobs Windows Transport et Commerce ont également terminé en succès ; leurs artefacts sont archivés dans le run #797.

## Correction de l'attribution des transactions — 28/11/2026

La relecture a révélé un défaut de diagnostic, pas un défaut métier : la durée d'un bloc `atomic()` ouvert pendant `setUpClass()` était étiquetée avec le contexte actif au moment de sa fermeture (`tearDownClass()`). Django 6.1.3 documente que `TestCase` conserve un bloc transactionnel pour toute la classe et un second par test. La durée de l'atomic de classe doit donc rester attribuée à son contexte d'ouverture, et ne pas être présentée comme un coût de teardown.

Correction : le runner mémorise désormais le nom du test/fixture à l'entrée de chaque `Atomic`, puis réutilise ce propriétaire lors de l'agrégation de sa durée totale. Le temps propre de `atomic_exit` reste, lui, attribué au contexte de fermeture.

Deuxième précision : une exception propagée dans le contexte de `Atomic.__exit__` déclenche normalement un rollback attendu. Elle ne signifie pas que la méthode SQL a elle-même échoué. Les métriques séparent maintenant `err` (exception réellement levée par l'opération instrumentée) et `exception_context` (exception présente dans le bloc, souvent attendue par le test).

Tests ajoutés : attribution explicite à `setUpClass`, distinction erreur SQL/contexte d'exception, et transmission du propriétaire du scope transactionnel. Le timeout GNU de 16 minutes, le comportement transactionnel Django et le code métier ne changent pas.

Référence officielle : Django 6.1.3, documentation « Testing tools » — `TestCase` enveloppe la classe entière et chaque test dans deux blocs `atomic()` imbriqués : https://docs.djangoproject.com/en/6.1/topics/testing/tools/#testcase
