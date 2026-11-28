# Validation SQL Server et sous-phases de simulation — 28/11/2026

## Dernière CI complète acquise avant l'instrumentation détaillée

Run [#884](https://github.com/piala00/YSFTEST/actions/runs/46146380871), commit testé
`d2ded55855bdd46d84897ee9b61a83032bbf2a1b` : **9/9 jobs terminés en succès**.

Les jobs récupérés depuis GitHub Actions confirment :
- Linux/SQLite : 834 tests réussis, 18 ignorés, 201,724 s.
- SQL Server shard 0 : 329 tests, 333,824 s ; création de la base 13,172 s ; destruction 3,793 s.
- SQL Server shard 1 : 505 tests, 522,392 s ; création de la base 18,563 s ; destruction 3,834 s.
- Clôture annuelle N→N+1 : 14/14 tests réussis en 63,929 s sur deux bases Django réellement migrées.
- Windows Transport et Commerce : compilation native, démarrage, installation Inno Setup, vrai clic « Copier le code », vérification du presse-papiers, installation en service, mise à jour et désinstallation réussis.
- Activation compilée, licences, guichet Chromium et simulation de volume : succès.

Le délai GNU reste exactement :
`timeout --verbose --signal=TERM --kill-after=30s 16m python -u tests_navigateur/sqlserver_test_runner.py`.
Aucun timeout n'a été augmenté.

## Diagnostic mesuré de la simulation multi-mois dans #884

Test : `apps.transport.tests.SimulationPlusieursMoisTests.test_jusqu_a_une_date_le_dernier_mois_s_arrete_a_ce_jour`.

- Corps du test : 95,478 s.
- 61 journées : 91,040 s cumulées, soit 1,492 s/jour en moyenne.
- Fins de mois : 2,355 s cumulées sur 3 appels.
- Initialisation : 1,388 s.
- Bilan et contrôles : 0,685 s.
- `cursor_execute` du test : 114 374 appels, 44,894 s cumulées.
- Connexions du shard 0 : 93 ouvertures / 96 fermetures comptabilisées dans le résumé global, 0,162 s d'ouverture et 0,025 s de fermeture cumulées. Les mesures de connexion ne constituent pas le goulot.

Les scopes `atomic` sont inclusifs et imbriqués : leurs sommes ne représentent pas du temps mural additionnel.

### Exception SQL attribuée

Le marqueur `[SQL-DB-EXCEPTION]` du shard 0 identifie :
`apps.comptabilite.tests_liaison.LiaisonComptableTests.test_T13_code_tiers_unique`.

Ce test attend explicitement une `IntegrityError` lors de la création d'un code tiers déjà utilisé, à l'intérieur de `assertRaises(IntegrityError)` et `transaction.atomic()`. Il s'agit d'un refus d'unicité attendu et testé, pas d'une erreur SQL inconnue à masquer.

## Instrumentation fine publiée sur la tête de PR

La tête de PR avant cette mise à jour documentaire est
`c665411870cdd8d3504f244765bdd34136675a32`.

Le code de `apps/transport/management/commands/simulation.py` ajoute :
- `[SIM-JOURNEE-PHASE]` pour achats/préparation, billets et colis, scénarios avant départ, départs/carburant/arrivées et opérations de fin de journée ;
- `[SIM-DETAIL-TOTAL]` pour les agrégats par sous-phase, ventes, chargements et opérations transport ;
- des mesures inclusives séparées du profil SQL exhaustif ;
- le profil SQL exhaustif reste opt-in via `SIMULATION_SQL_DIAGNOSTIC=1`, sans être activé par `SQL_TEST_TIMINGS=1`.

Le test `SimulationPlusieursMoisTests.test_deux_mois_a_cheval_sur_deux_annees` force explicitement
`SIMULATION_SQL_DIAGNOSTIC=0` tout en activant `SQL_TEST_TIMINGS=1`, puis vérifie les marqueurs de détail des journées, des ventes et des départs.

**Limite de preuve :** le run #884 teste le commit antérieur `d2ded558`. Il ne valide pas encore la tête `c6654118` ni les nouveaux marqueurs détaillés. Le prochain run complet déclenché par cette mise à jour doit confirmer leur présence dans les logs SQL Server et répéter les neuf jobs.

## Suite de travail

1. Vérifier la CI complète sur la nouvelle tête de branche.
2. Extraire les `[SIM-JOURNEE-PHASE]` et `[SIM-DETAIL-TOTAL]` du test de 61 jours.
3. Corriger uniquement la sous-phase métier démontrée dominante ; comparer avant/après sur SQL Server.
4. Garder le timeout de 16 minutes, les transactions et les règles comptables inchangés.
5. Répéter P0.3 et la recette Windows native sur le même SHA.

Aucune fusion, aucun déploiement, aucune donnée réelle et aucune identité privée ne sont concernés.
