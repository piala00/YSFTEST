# Mesures et rééquilibrage SQL Server — 28 novembre 2026

## Référence vérifiée

- Dépôt : `piala00/YSFTEST`
- Branche de développement : `gpt/analytique-service-paie-20261128`
- Branche cible : `ccr-5592a371-fusjt2`
- CI complète #754 : succès, 9 jobs sur 9.
- Commit testé : `67b52c563153fa1c14d9494fd755e4149e064da6`
- Moteur : SQL Server 2022, un conteneur jetable par shard.

## Relecture du timeout historique #381

Le journal original du job `128230852957` a été récupéré et relu, pas seulement son résumé GitHub.

- La commande démarre à `00:11:49.628Z`.
- `timeout` envoie TERM à `00:27:49.648Z`, soit exactement la limite de 16 minutes.
- Le dernier test affiché démarre à `00:27:45.381Z` : `ChoixDeBaseALInstallationTests.test_sqlserver_injoignable_retour_sur_sqlite`. Il n'a donc que 4,3 secondes d'exécution avant l'arrêt ; le journal ne prouve pas qu'il soit lui-même lent ou bloqué.
- Un dump de pile à `00:23:49.674Z` montre la simulation multi-mois dans `simulation.py:124`, au traitement de fin de mois (`fin_de_mois`), puis `Decompte.calculer` → `Decompte.evaluer` → `ParametresTransport.get` → `mssql_python.cursor.execute`. Le test concerné termine ensuite à `00:23:58.955Z` : ce dump est un instantané d'un scénario coûteux, pas la preuve d'une requête bloquée.
- Le serveur SQL poursuit ses opérations de démarrage, sauvegarde et restauration ; aucune erreur SQL Server n'explique le code 124 dans ce journal.

Conclusion étayée : #381 est d'abord un dépassement **cumulatif** de la suite monolithique de 16 minutes. Le dernier test est seulement celui qui était en cours à l'échéance. La simulation multi-mois et plusieurs scénarios d'intégration consomment une part importante du budget. La séparation en deux conteneurs/shards et l'équilibrage des classes traitent cette cause sans masquer l'échec ni relever le timeout.

## Mesures des deux shards

| Mesure | Shard 0 | Shard 1 |
|---|---:|---:|
| Tests découverts/exécutés | 317 | 506 |
| `run_suite` | 558,881 s | 374,638 s |
| `setup_databases` | 22,766 s | 12,664 s |
| `teardown_databases` | 4,723 s | 3,720 s |
| Connexions ouvertes (durée cumulée) | 0,333 s | 0,181 s |
| Fermetures (durée cumulée) | 0,043 s | 0,023 s |

Les ouvertures/fermetures de connexions ne sont pas le goulot mesuré. La création de la base de test coûte environ 13 à 23 secondes et sa destruction 4 secondes : coûts visibles, mais très inférieurs aux scénarios métier les plus longs.

## Tests et classes dominants

- `SimulationPlusieursMoisTests.test_jusqu_a_une_date_le_dernier_mois_s_arrete_a_ce_jour` : 163,811 s.
- `SimulationPlusieursMoisTests.test_deux_mois_a_cheval_sur_deux_annees` : 22,175 s.
- Transaction de classe observée pour `SimulationPlusieursMoisTests` : 191,265 s.
- `DemandesDeCorrectionTests.test_signaler_corriger_contester_annuler` : 33,829 s.
- `MiroirTests.test_copie_complete_puis_refus_d_une_base_etrangere` : 28,191 s.
- `BaseSQLServerTests.test_sqlite_vers_sqlserver_puis_gestion_et_retour` : 32,014 s.
- `AdministrationOngletsTests.test_colonne_absente_signalee_sans_recreation` : 26,969 s.
- `ScenarioTroisDossiersTests.test_billets_colis_entre_agences_et_consolidation` : 20,991 s.
- `DossierGenereReelTests.test_generation_rapide_export_import_et_ouverture_meme_adresse` : 19,915 s.

Les mesures `atomic` sont inclusives et imbriquées, donc ne doivent pas être additionnées comme du temps CPU. La documentation officielle Django 6.1 précise que `TestCase` enveloppe la classe entière et chaque test dans deux blocs `atomic()` imbriqués ; la durée de l'atomic de classe reflète donc notamment la durée de vie de la classe, pas une attente SQL équivalente. Source : https://docs.djangoproject.com/en/6.1/topics/testing/tools/#testcase

## Correction d'ordonnancement

Le runner conserve les classes entières (pas de découpage de `setUpClass`/`tearDownClass`) et réaffecte les charges observées :

- `SimulationPlusieursMoisTests` : shard 0 → shard 1.
- `BaseSQLServerTests`, `AdministrationOngletsTests`, `ScenarioTroisDossiersTests`, `DossierGenereReelTests` : shard 1 → shard 0.
- Les autres overrides restent inchangés.

Estimation simple à partir des durées #754 :
- shard 0 : 558,881 - 191,265 + 32,014 + 26,969 + 20,991 + 19,915 = **467,505 s** ;
- shard 1 : 374,638 + 191,265 - 32,014 - 26,969 - 20,991 - 19,915 = **466,014 s**.

Cette estimation ne remplace pas la prochaine mesure CI. Elle ne change ni le délai de 16 minutes ni le contenu des tests ; elle équilibre les classes coûteuses observées.

## SIGSEGV / timeout

Sur #754, les deux shards ont terminé sans code 124/137 et sans trace SIGSEGV. Le test ciblé de reprise Sage a été reproduit en 1,151 s avant la suite complète du shard 1.

Cela confirme l'absence de reproduction sur cette exécution, mais ne prouve pas qu'un crash intermittent est impossible. Le diagnostic de core dump/GDB reste activé sur échec. Le watchdog par test/fixture ne tue pas les tests ; il fournit une trace après le seuil configuré.

## Prochaine vérification

Le prochain run doit confirmer :
1. l'équilibre réel des deux shards ;
2. la réussite des deux suites SQL Server complètes sous le timeout existant de 16 minutes ;
3. l'absence de SIGSEGV ;
4. la réussite de la suite Linux, de la clôture N→N+1 et des recettes Windows.

Aucune fusion ni aucun déploiement n'est effectué.
