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


## Validation du correctif transactionnel — run #805, 28/11/2026

Le run [#805](https://github.com/piala00/YSFTEST/actions/runs/46106549509) a terminé avec **9 jobs sur 9 en succès**. Les deux shards SQL Server ont émis leurs marqueurs de synthèse et archivé leurs journaux.

| Mesure du run #805 | Shard 0 | Shard 1 |
|---|---:|---:|
| Tests | 317 | 505 |
| `run_suite` | 318,925 s | 690,866 s |
| `setup_databases` | 12,350 s | 25,031 s |
| `teardown_databases` | 4,834 s | 3,886 s |
| Ouverture des connexions (cumul) | 0,158 s | 0,278 s |
| Fermeture des connexions (cumul) | 0,024 s | 0,044 s |
| Appels `cursor_execute` | 330 160 | 256 756 |
| Temps `cursor_execute` cumulé | 139,698 s | 250,503 s |

Les durées `atomic_scope` sont inclusives et imbriquées : 922,171 s sur le shard 0 et 1 211,123 s sur le shard 1. Elles ne sont pas additionnables au temps mural. Le test de simulation le plus long du shard 0 est `test_jusqu_a_une_date_le_dernier_mois_s_arrete_a_ce_jour` (91,714 s selon `TestCase.run`). Le journal du shard 1 montre notamment des fixtures de classe coûteuses : AdministrationOnglets (63,524 s inclusifs), PagesEtApi (54,827 s) et PlanAnalytiqueComplet (60,395 s).

La suite SQLite a exécuté 822 tests en 133,993 s (18 ignorés). La recette P0.3 sur deux bases Django réellement migrées a exécuté 14 tests en 51,369 s. Les deux shards SQL Server, les deux recettes Windows, l'activation compilée, le guichet, les licences et la simulation volume sont en succès. Le délai GNU de 16 minutes n'a pas été modifié.

## Séparer les métriques du runner du profil SQL exhaustif de simulation

La lecture du code de `apps/transport/management/commands/simulation.py` a montré que `SQL_TEST_TIMINGS=1`, posé par le runner CI, activait aussi un `connection.execute_wrapper` dans chaque journée simulée. Ce profil détaillé conserve les formes SQL, agrège chaque requête et calcule des empreintes SHA-256. Il est utile pour une enquête ciblée, mais ne doit pas être activé implicitement pendant toute la suite.

Correction proposée et publiée dans le commit suivant la validation #805 :
- `SQL_TEST_TIMINGS` conserve les mesures générales du runner SQL Server (test, corps, fixtures, connexions, curseurs et transactions).
- Le profil exhaustif de la commande de simulation dépend désormais de `SIMULATION_SQL_DIAGNOSTIC=1` (valeurs explicites acceptées : `1`, `true`, `yes`, `on`).
- Les mesures quotidiennes métier `self.mesures` restent présentes ; seule l'instrumentation SQL détaillée est opt-in.
- Le calcul de trésorerie ne déclenche plus son sous-profileur lorsque seul le runner CI est actif.

Tests ciblés ajoutés : `DiagnosticSqlSimulationTests` vérifie que `SQL_TEST_TIMINGS` seul n'active pas le profileur, que la variable dédiée l'active, et que les valeurs désactivantes le maintiennent éteint. Le workflow exécute ce groupe séparément avant la suite SQLite. Le comparatif de performance A/B reste à obtenir dans le run qui suit ce commit ; aucun gain n'est revendiqué avant cette mesure.

Aucun changement de logique comptable, de transactions, de scénario métier ou de délai d'exécution n'est introduit par cette séparation.


## Analyse détaillée du run #878 — 28/11/2026

Le run [#878](https://github.com/piala00/YSFTEST/actions/runs/46139965308) a terminé **9 jobs sur 9 en succès** sur le commit `db0210f1e8fcb39b651485a64e98dff24efc4602`. Les deux shards SQL Server sont restés très en dessous du timeout GNU de 16 minutes :

| Mesure #878 | Shard 0 | Shard 1 |
|---|---:|---:|
| Tests exécutés | 328 | 505 |
| `run_suite` | 345,151 s | 379,633 s |
| `setup_databases` | 13,460 s | 12,553 s |
| `teardown_databases` | 3,881 s | 3,695 s |
| Ouvertures de connexions cumulées | 0,164 s | 0,148 s |
| Fermetures cumulées | 0,026 s | 0,023 s |
| `cursor_execute` | 330 160 appels / 152,869 s | 256 749 appels / 134,253 s |

### Cause mesurée du test de simulation le plus long

`apps.transport.tests.SimulationPlusieursMoisTests.test_jusqu_a_une_date_le_dernier_mois_s_arrete_a_ce_jour` a pris **99,000 s dans son corps**. La simulation exécute 61 journées (01/01/2026 au 02/03/2026) :

- Temps cumulé des journées : 94,316 s ; moyenne 1,546 s/jour.
- Journée la plus courte : 0,877 s ; la plus longue : 2,159 s.
- Les phases initialisation, fins de mois et bilan expliquent le reste.
- Le test porte 114 374 appels `cursor_execute`, pour 46,316 s cumulées dans le wrapper SQL.
- Les connexions ne sont pas le goulot : leur coût cumulé est inférieur à 0,2 s par shard.

Le scope `atomic` attribué à `setUpClass` dure 119,878 s, mais il s'agit de la transaction de classe qui reste ouverte pendant les tests, pas de 119 s de préparation. La documentation officielle Django 6.1 indique que `TestCase` ouvre deux blocs `atomic()` imbriqués, l'un pour la classe et l'autre pour chaque test : https://docs.djangoproject.com/en/6.1/topics/testing/tools/#testcase

Un compteur `cursor_execute err=1` apparaît encore dans le résumé du shard 0, sans ligne `[SQL-DB-EXCEPTION]` correspondante. Aucun test n'a échoué. Il reste à attribuer cet écart entre le compteur et le journal d'exception ; il n'est pas classé comme erreur métier résolue.

### Instrumentation publiée après #878

Les commits suivants ajoutent un profilage léger, sans `execute_wrapper` et sans changer les transactions métier :

- `e4e0e4a9` : sous-phases quotidiennes (achats, billets/colis, scénarios, départs/carburant/arrivées, opérations de fin de journée), ventes, chargements et opérations transport.
- `0e911930` : test de parcours multi-mois vérifiant les marqueurs agrégés.
- `0b99da8d` : test unitaire d'agrégation des sous-phases.
- `fb4786b1` : séparation des agrégats détaillés du profileur SQL exhaustif ; évite de mélanger les dictionnaires des phases globales avec les anciennes listes des sous-phases.

Les marqueurs attendus sont `[SIM-JOURNEE-PHASE]` et `[SIM-DETAIL-TOTAL]`. Les temps des sous-phases sont inclusifs et peuvent se recouvrir ; ils ne doivent pas être additionnés au temps total du jour. Ces changements sont publiés sur la branche de travail, mais **ne sont pas encore validés par une nouvelle exécution GitHub Actions**. Aucun gain de performance n'est revendiqué avant l'analyse des nouvelles traces.

La branche de travail reste distincte de `ccr-5592a371-fusjt2`. Aucun rebase, fusion vers la cible ou déploiement n'a été effectué.
