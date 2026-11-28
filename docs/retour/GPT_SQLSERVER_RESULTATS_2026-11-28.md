# Relevé SQL Server #878 et correction ciblée — 28/11/2026

## Preuve de référence

Le run [GitHub Actions #878](https://github.com/piala00/YSFTEST/actions/runs/46139965308), commit
`db0210f1e8fcb39b651485a64e98dff24efc4602`, a terminé avec **9 jobs sur 9 en succès**.
La limite de 16 minutes du runner SQL Server n'a pas été modifiée.

| Mesure | Shard 0 | Shard 1 |
|---|---:|---:|
| Tests | 328 | 505 |
| Durée de suite | 345,151 s | 379,633 s |
| Création de base (appel public) | 13,460 s | 12,553 s |
| Destruction de base | 3,881 s | 3,695 s |
| Connexions ouvertes | 95 | 100 |
| Temps cumulé ouverture | 0,252 s | 0,185 s |
| Connexions fermées | 95 | 100 |
| Temps cumulé fermeture | 0,026 s | 0,023 s |

Les connexions ne sont pas le goulot : ouverture et fermeture cumulées restent sous 0,3 seconde par shard.
Le shard 0 exécute 328 tests en 345,151 secondes ; le shard 1 exécute 505 tests en 379,633 secondes.

## Simulation multi-mois : ce que montrent réellement les phases

Le test le plus long du shard 0 est
`SimulationPlusieursMoisTests.test_jusqu_a_une_date_le_dernier_mois_s_arrete_a_ce_jour` :
99,000 secondes, pour 61 jours simulés du 1er janvier au 2 mars 2026 (janvier 31 jours,
février 28, mars 2).

Les traces `[SIM-PHASE]` montrent :
- Initialisation : 1,495 s.
- Chaque journée : environ 0,877 à 2,159 s.
- Fin de mois : 0,773 à 0,904 s par mois.
- Bilan et contrôles : 0,730 s.

La durée est répartie sur les opérations métier quotidiennes ; aucune attente de connexion
n'explique ces 99 secondes. Une optimisation des règles métier ou des requêtes ne sera engagée
qu'après identification d'une phase dominante par des mesures agrégées, sans remplacer les
moteurs de validation comptable par des écritures directes.

Le profilage SQL exhaustif reste désactivé dans la CI normale. Le chronométrage léger
`SQL_TEST_TIMINGS` active les phases et leurs totaux par famille (`journee`, `fin_de_mois`,
`initialisation`, `bilan_et_controles`) ; il n'active pas `execute_wrapper`.

## Clarification des transactions Django TestCase

Dans le journal shard 0, une transaction attribuée à
`setUpClass apps.transport.tests.SimulationPlusieursMoisTests` durait 119,878 s.
Le marqueur `[SQL-FIXTURE-END]` indiquait pourtant 0,002 s pour l'exécution réelle de
`setUpClass`. La transaction ouverte par `TestCase.setUpClass` enveloppe tous les tests
de la classe et se ferme dans `tearDownClass`. La durée de 119,878 s ne doit donc pas être
interprétée comme une préparation lente. Le runner la nomme désormais `transaction_classe`.

## Exception SQL isolée

Le résumé du shard 0 indique une exception sur un seul appel `cursor_execute` parmi 330 160 ;
le shard 1 ne signale aucune exception de curseur parmi 256 749 appels. Le résumé précédent ne
permet pas d'attribuer l'appel. Le runner ajoute `[SQL-DB-EXCEPTION]` avec opération, alias,
durée et test propriétaire, sans SQL ni paramètres. La prochaine CI dira si l'appel est un
refus attendu par un test négatif ou un défaut réel. Une exception interceptée n'est pas
automatiquement un échec de suite.

## Correctifs de ce lot

- Agrégation légère des phases de simulation même lorsque le profileur SQL exhaustif est désactivé.
- Attribution des transactions de classe Django sous `transaction_classe`.
- Journalisation sans données métier de l'opération SQL qui lève une exception.

## Garde-fous

Aucun timeout n'est augmenté ; aucune exception n'est ignorée ; aucun SQL ni paramètre n'est
journalisé ; aucune donnée réelle n'est utilisée. La nouvelle CI doit exécuter les tests ciblés,
les deux shards SQL Server sous 16 minutes, la suite SQLite, P0.3 sur bases Django réellement
migrées et les deux recettes Windows. Si `[SQL-DB-EXCEPTION]` révèle une exception métier
inattendue, corriger son origine avant de considérer le chantier clos.
