# Correction du test de trace de simulation sous runner — 28/11/2026

## Échec constaté dans la CI #880

Run : https://github.com/piala00/YSFTEST/actions/runs/46144850397

Deux échecs partageaient le même défaut de test :

- Linux : `DiagnosticSqlSimulationTests.test_trace_de_phase_visible_dans_la_sortie_du_runner` échouait avec `AssertionError: None != 2.5`.
- SQL Server shard 0 : le même test échouait avec `AssertionError: 1230.472348426 != 2.5`.

Le shard SQL Server 1, les deux jobs Windows, l'activation compilée, les licences, le guichet et la simulation de volume ont réussi. Les jobs Windows ont notamment passé le vrai clic « Copier le code », l'installation/mise à jour/désinstallation et la compilation.

## Cause racine

Le test appelait `tracer_phase_sql` une première fois dans le contexte où `SQL_TEST_TIMINGS=1`, `time.perf_counter` était simulé et la sortie capturée, puis une seconde fois après la sortie de ces patches.

La seconde invocation n'était donc pas déterministe :

- hors runner, `SQL_TEST_TIMINGS` est absent : la fonction renvoie `None` ;
- dans le runner SQL Server, `SQL_TEST_TIMINGS=1` : la fonction mesure le vrai temps écoulé depuis le repère artificiel `10.0`, d'où environ 1 230 secondes.

Le code métier de simulation n'était pas en cause. Le test mélangeait deux environnements différents et vérifiait une seconde invocation non contrôlée.

## Correctif publié

Commit : `8328e07b7beb1959709a7f6d75396a22dbeb8e02`

Dans `apps/transport/tests_simulation_metier.py`, le test capture désormais la valeur retournée lors de l'unique invocation effectuée à l'intérieur du contexte déterministe, puis vérifie cette valeur (`2.5`) et la ligne écrite. Il n'effectue plus de second appel après restauration de l'environnement et de l'horloge.

Le test distinct `test_trace_de_phase_absente_hors_instrumentation` continue de vérifier que la trace est absente et que l'horloge n'est pas appelée lorsque l'instrumentation est désactivée.

## Exception SQL observée : attribution vérifiée

Le compteur SQL du shard 0 signalait une exception sur un appel `cursor_execute`. Le marqueur d'attribution identifie :

`apps.comptabilite.tests_liaison.LiaisonComptableTests.test_T13_code_tiers_unique`

Le code de ce test contient explicitement :

```python
with self.assertRaises(IntegrityError), transaction.atomic():
    Tiers.objects.create(code="CLIA", nom="Autre client homonyme de code")
```

L'exception est donc le refus attendu de la contrainte d'unicité, vérifié par le test. Ce n'est pas une erreur SQL inattendue à masquer. Le marqueur d'instrumentation conserve précisément le test propriétaire.

## Validation attendue

La nouvelle CI déclenchée par le commit doit confirmer :

- le test ciblé sur Linux ;
- le même test dans le shard SQL Server 0 ;
- les deux suites SQL Server sous le timeout de 16 minutes, inchangé ;
- la suite SQLite et la clôture N→N+1 sur deux bases Django réellement migrées ;
- les deux recettes Windows, dont le vrai clic du wizard Inno Setup.

Aucun timeout n'est augmenté. Aucune exception n'est ignorée. Aucune fusion, aucun déploiement et aucune donnée réelle ne sont concernés.
