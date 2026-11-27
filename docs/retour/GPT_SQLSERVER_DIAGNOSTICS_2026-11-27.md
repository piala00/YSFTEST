# Diagnostic SQL Server et continuité P0.3 — 27/11/2026

## Référence vérifiée

- Dépôt : `piala00/YSFTEST`.
- Branche de travail d'origine : `ccr-5592a371-fusjt2`.
- SHA contrôlé : `6d1225e51ec6b00c23dd83dc5f2c2292c26c596d`.
- Contrôle GitHub Actions #640 : run `46026041243`, conclusion `success`, neuf jobs terminés.
- Contrôle de clôture SQLite #85 : run `46026041360`, conclusion `success`.

## Preuves du run #640

Les deux jobs SQL Server 2022 ont exécuté toute la suite répartie par classes, sans couper une classe entre shards :

| Shard | Tests | Durée de la suite | Résultat |
|---|---:|---:|---|
| 0 | 311 | 522,675 s | OK |
| 1 | 491 | 394,347 s | OK |

Les journaux montrent les phases `setup_databases`, `run_suite` et `teardown_databases`, les durées de chaque test, de son corps, des fixtures et des classes. Les bases de test sont détruites à la fin des deux jobs. Le test métier le plus long du shard 0 est la simulation pluri-mensuelle à 128,581 s ; il se termine normalement. Sur le shard 1, les deux tests les plus longs sont la bascule SQLite/SQL Server (39,925 s) et la vérification de colonnes absentes (35,839 s).

La limite de 16 minutes n'a pas été augmentée. Le runner conserve l'affectation stable par classe et les deux shards parallèles ; le résultat CI confirme que l'ordonnancement tient dans le délai existant.

## Instrumentation ajoutée sur cette branche GPT

Le runner `tests_navigateur/sqlserver_test_runner.py` mesure maintenant, en plus des tests et fixtures :

- `ensure_connection`, `connect`, `close` ;
- `commit`, `rollback` ;
- entrée et sortie de `transaction.atomic`, durée totale du bloc, profondeur imbriquée et exception.

Les métriques sont agrégées par alias de base et par test. Les journaux ajoutent les marqueurs `[SQL-DB-SUMMARY]` et `[SQL-DB-TEST-TOP]`. Aucun paramètre SQL ni valeur métier n'est journalisé. Les wrappers conservent le retour et les exceptions des méthodes instrumentées ; ils ne changent ni la stratégie transactionnelle ni les données.

Les tests unitaires couvrent l'agrégation, la conservation du retour et la propagation des erreurs. La CI de cette branche doit encore confirmer l'intégration avec le vrai SQL Server.

## Clôture annuelle P0.3 / P0.4

Le job Linux du run #640 a terminé l'étape « Clôture N vers N+1 sur deux bases réellement migrées ». Le job Windows Transport a terminé l'étape « Clôture annuelle depuis l'EXE natif puis redémarrage sur N+1 ». Les jobs SQL Server 2022 ont également réussi. Cela valide les parcours CI présents ; cela ne remplace pas un essai sur le poste réel du propriétaire avec son identité d'éditeur.

## Rectification du point CAN

Le canal de vente n'est pas un champ manquant à ajouter à `Billet` ou `Colis`. Le plan `points_vente` existe dans `apps/comptabilite/plan_analytique.py` ; la recette de chaque départ est répartie selon le point de vente de chaque billet. `docs/retour/analytique/ECARTS_A_CORRIGER.md` classe déjà les canaux de vente comme faits depuis le 26/10/2026. Ajouter un second champ `canal_vente` créerait deux sources de vérité et risquerait de doubler la recette analytique.

## Écarts fonctionnels encore explicitement documentés

L'audit `docs/retour/AUDIT_ECARTS.md` signale notamment les quotas de sièges inter-agences, la tournée courrier distincte, le registre des immobilisations/amortissements, le périmètre de droits par agence et le rapprochement fournisseur en trois pièces. Les allocations fractionnées de charges communes restent également en attente des charges et clés validées. Ces sujets ne sont pas codés dans cette tranche : ils nécessitent des règles opérationnelles ou comptables explicites et ne doivent pas être inventés.

## Suite

1. Lire les nouveaux marqueurs de connexions et transactions sur les deux shards de la CI GPT.
2. Comparer leurs totaux et leurs maxima avec les durées de tests/fixtures ; ne déplacer une classe que sur mesures.
3. Garder P0.3/P0.4 verrouillés par les tests déjà présents.
4. Choisir le prochain lot métier à partir des exigences validées, sans réintroduire un champ CAN redondant.
## Référence technique officielle

La documentation Django 6.1, consultée le 27/11/2026, confirme que `TestCase` enveloppe chaque test dans une transaction et que les blocs `atomic()` imbriqués utilisent des savepoints, libérés ou annulés à la sortie ; la transaction externe est ensuite validée ou annulée. L'instrumentation mesure donc les scopes `atomic`, leur imbrication, les savepoints et les opérations de commit/rollback séparément, sans changer la sémantique transactionnelle : https://docs.djangoproject.com/en/6.1/topics/db/transactions/ (sections « Controlling transactions explicitly », « Savepoints » et « Use in tests »).

## Analyse du job #381 à partir des logs bruts

- Le processus démarre les tests vers `00:12:17Z` et reçoit TERM à `00:27:49Z`, soit 16 minutes après le démarrage du runner.
- 565 tests avaient commencé ; le dernier, `ChoixDeBaseALInstallationTests.test_sqlserver_injoignable_retour_sur_sqlite`, venait de démarrer au moment du TERM. Le log ne prouve donc pas que ce dernier test était bloqué.
- Les messages `Timeout (0:02:00)!` sont des dumps périodiques de `faulthandler`, pas le timeout global de la commande.
- Les plus longues séquences observées sont la simulation multi-mois (~146,855 s), la bascule SQLite/SQL Server (~50,888 s), et des tests de pages/administration (~57 s et ~35 s). Aucun de ces tests n'explique seul les 16 minutes.
- La création de `test_ERP_ESSAI` et de `ERP_ESSAI_BASCULE_8b14fa`, les sauvegardes/restaurations et DBCC sont visibles dans le log ; la sauvegarde/restauration de la base de bascule prend quelques dizaines de millisecondes. Le conteneur SQL Server est éphémère et est arrêté avec le job.

Conclusion : l'échec #381 était d'abord un dépassement de durée cumulée de la suite séquentielle, pas un test isolé de 16 minutes. Le découpage stable par classe en deux shards est le correctif d'ordonnancement ; il garde la limite interne de 16 minutes.

## Résultats du run #649 avec la première instrumentation

- Run #649 : `46033198425`, commit `0d7dc4e77dfc1c46f9185c73b73f1819fa35bcdf`, neuf jobs réussis.
- SQL Server shard 0 : 311 tests, `run_suite=614,125 s`, `setup_databases=20,023 s`, `teardown_databases=3,576 s`.
- SQL Server shard 1 : 491 tests, `run_suite=541,151 s`, `setup_databases=21,463 s`, `teardown_databases=3,825 s`.
- Les deux commandes sont restées sous le timeout de 16 minutes ; aucun test SQL Server n'a échoué.
- Le rapport de métriques à la sortie a cependant révélé un défaut du diagnostic : `Atomic(using=None)` produit un alias `None`, et le tri des alias `None`/chaînes levait un `TypeError`. Les tests n'étaient pas en échec, mais les métriques connexions/transactions n'étaient pas imprimées.

Correctif appliqué ensuite sur cette branche : normaliser `using=None` vers l'alias Django `default`, trier les alias par leur représentation texte et couvrir ce cas par un test unitaire. Le run #650 doit confirmer la présence effective de `[SQL-DB-SUMMARY]` et `[SQL-DB-TEST-TOP]` ; ne pas considérer la télémétrie comme validée avant ces marqueurs.

## Détail du backend SQL Server

La CI #640 a installé Django 6.1.3, mssql-django 2.0.0 et mssql-python 1.19.0. Le code tagué mssql-django 2.0.0 appelle `SELECT @@TRANCOUNT` dans `_set_autocommit`, `_savepoint` et `_savepoint_rollback`. Dans le test de simulation analysé, 3 437 requêtes SQL ont consommé environ 2,055 s au total ; `SELECT @@TRANCOUNT` représente 391 appels et environ 0,135 s, sans requête individuelle supérieure à 0,5 s. Ce motif est donc une activité de gestion transactionnelle du backend, pas la preuve d'une attente SQL de plusieurs minutes.

Sources de version :
- [Django 6.1 — transactions et savepoints](https://docs.djangoproject.com/en/6.1/topics/db/transactions/)
- [mssql-django 2.0.0 — backend SQL Server](https://github.com/microsoft/mssql-django/blob/2.0.0/mssql/base.py)

Les savepoints ne doivent pas être désactivés à l'aveugle : les blocs `atomic()` imbriqués protègent les retours arrière partiels. La prochaine analyse doit comparer les durées cumulées `atomic_scope`, `set_autocommit`, `savepoint`, `commit` et `rollback` produites par le run #650 avant toute optimisation métier.
