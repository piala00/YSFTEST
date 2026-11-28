# Diagnostic SQL Server et sous-phases de simulation — 28/11/2026

## CI complète #896 — commit vérifié

Run [#896](https://github.com/piala00/YSFTEST/actions/runs/46154678964), SHA
`9222d23b037f0178ebfdb33c6d7db97b9d62bc87` : **9/9 jobs terminés en succès**.

- SQL Server shard 0 : 330 tests en 428,749 s.
- SQL Server shard 1 : 505 tests en 553,084 s.
- Le timeout de la suite SQL Server reste exactement
  `timeout --verbose --signal=TERM --kill-after=30s 16m python -u tests_navigateur/sqlserver_test_runner.py`.
- Linux/SQLite : 835 tests réussis, 18 ignorés, en 129,328 s.
- Clôture N→N+1 : 14/14 tests en 50,032 s sur deux bases Django réellement migrées.
- Windows Transport et Commerce : compilation native, démarrage, clôture depuis l'EXE Transport, installateur Inno Setup, vrai clic « Copier le code », comparaison du presse-papiers, service, mise à jour et désinstallation réussis.
- Activation compilée, licences, guichet Chromium et simulation de volume : succès.

Les jobs récupérés auprès de GitHub Actions sont tous en état `completed/success`. Ce résultat valide SHA `9222d23b`, pas les commits publiés après ce run.

## Simulation de 61 journées — mesures réelles du shard SQL Server 0

Test :
`apps.transport.tests.SimulationPlusieursMoisTests.test_jusqu_a_une_date_le_dernier_mois_s_arrete_a_ce_jour`.

- Corps du test : 126,978 s.
- 61 journées : 121,119 s cumulées, soit 1,986 s/jour en moyenne.
- Fins de mois : 3,034 s sur 3 appels.
- Initialisation : 1,891 s.
- Bilan et contrôles : 0,924 s.
- `cursor_execute` : 114 374 appels, 59,518 s cumulées.
- `ensure_connection` : 144 108 appels, 0,164 s cumulées ; l'ouverture/fermeture des connexions n'explique pas le temps mural.

### Phases journalières

| Phase | Appels | Temps cumulé |
|---|---:|---:|
| Départs, carburant et arrivées | 61 | 62,722 s |
| Billets et colis | 61 | 45,049 s |
| Opérations de fin de journée | 61 | 11,332 s |
| Préparation et achats | 61 | 1,942 s |
| Scénarios avant départ | 61 | 0,067 s |

### Sous-phases métier

| Opération | Appels | Temps cumulé |
|---|---:|---:|
| Départ du véhicule | 574 | 33,917 s |
| Carburant et caisse | 574 | 26,080 s |
| Vente de billets | 461 | 28,265 s |
| Enregistrement des colis | 266 | 11,215 s |
| Chargement des colis | 266 | 2,239 s |
| Arrivée | 574 | 1,572 s |

`vente.transaction_depart` totalise 45,041 s sur 574 transactions ; cette mesure englobe les opérations de vente effectuées dans chaque transaction. Elle ne doit pas être additionnée à `vente.billet_vendre`.

Les scopes `atomic` sont imbriqués et inclusifs : les 356,597 s cumulées sur 13 896 scopes atomiques du test ne représentent pas 356 secondes murales supplémentaires. La transaction de classe de `TestCase` couvre aussi la durée de vie des tests de la classe.

### Conclusion provisoire

Le coût se concentre dans les opérations métier répétées de départ, carburant/caisse et vente de billets. Les connexions ne sont pas le goulot. Les métriques légères ne suffisent toutefois pas à distinguer les requêtes ORM répétées à l'intérieur de ces opérations ; aucune optimisation métier n'est appliquée avant cette attribution.

## Exception SQL observée

Le marqueur `[SQL-DB-EXCEPTION]` identifie
`apps.comptabilite.tests_liaison.LiaisonComptableTests.test_T13_code_tiers_unique`.
Ce test attend une `IntegrityError` lors de la création d'un code tiers déjà utilisé, dans un `assertRaises(IntegrityError)` et une transaction atomique. C'est le refus d'unicité attendu par le test, pas une erreur silencieuse à supprimer.

## Instrumentation légère publiée

La tête de PR ajoute dans `apps/transport/management/commands/simulation.py` :

- `[SIM-JOURNEE-PHASE]` : achats/préparation, billets/colis, scénarios, départs/carburant/arrivées et fin de journée ;
- `[SIM-DETAIL-TOTAL]` : agrégats par sous-phase, ventes, chargements et opérations de transport ;
- agrégats légers distincts du profileur SQL exhaustif ;
- profileur SQL exhaustif activé uniquement par `SIMULATION_SQL_DIAGNOSTIC=1`.

Le test multi-mois vérifie les marqueurs détaillés tout en maintenant
`SIMULATION_SQL_DIAGNOSTIC=0` et `SQL_TEST_TIMINGS=1`.

## Profil SQL ciblé publié après #896

Commit `c353010fea996b5327c84da97608ed52540a743d` :
[ajout du profil SQL ciblé au workflow](https://github.com/piala00/YSFTEST/commit/c353010fea996b5327c84da97608ed52540a743d).

Le shard 0 exécute séparément le seul test de 61 journées avec
`SIMULATION_SQL_DIAGNOSTIC=1`, une borne de 7 minutes et l'archivage des signatures SQL par phase. La suite complète conserve son délai de 16 minutes ; aucun timeout n'a été relevé.

**Ce commit `c353010f` n'est pas encore validé par une CI récupérée.** Les signatures SQL ciblées doivent être lues avant de modifier `Billet.vendre`, `Depart.partir` ou `PleinCarburant.enregistrer`.

## Suite de travail

1. Vérifier la nouvelle CI sur `c353010f` et récupérer le profil SQL ciblé.
2. Identifier les formes SQL répétées dominantes par phase, sans paramètres ni données métier dans les logs.
3. Optimiser la lecture répétée démontrée, en conservant verrouillages, écritures, sessions de caisse et règles SYSCOHADA.
4. Rejouer le test ciblé, puis les deux shards SQL Server et les neuf jobs.
5. Répéter P0.3 et les recettes Windows sur le même SHA.

Aucune fusion, aucun déploiement, aucune donnée réelle et aucune identité privée ne sont concernés.
