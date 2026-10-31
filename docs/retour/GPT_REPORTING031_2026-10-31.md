# Reporting03.1 — accès à l'état des colis non livrés

Codex, 31 octobre 2026. Coordination : issue #24, commentaire 6547013470 ; exigence E-001 et demande NV-004 du pilotage #26.

## Changement

Depuis le produit validé de #28 (`ae724335d7117189378309eefbaa44e4fca3f3ce`), ajout du lien « Colis non livrés » à la famille Transport du catalogue des états. L'état existant est réutilisé : seuil de retard, ancienneté, gare d'arrivée, CSV, graphique `data-graphique`, menu et droits. Aucun nouveau moteur ni calcul financier.

## Vérifications exécutées

- `manage.py test apps.reporting --noinput` : 25 tests réussis, 44,987 s, aucun ignoré ; tests existants des menus et des colis réutilisés.
- Inspection avec le client HTTP Django sur une base SQLite temporaire fictive : un lien en activité Transport, aucun en activité Commerce ; dates `du`, `au`, `date_debut`, `date_fin` conservées ; rapport et CSV HTTP 200 contenant le colis fictif âgé de dix jours ; marqueur du graphique présent. Ce n'est pas une recette dans un navigateur Windows.
- Profil avec interdiction explicite de `transport.recettes.colis_non_livres` : rapport et CSV HTTP 403. Le même profil en lecture : HTTP 200 pour les deux. L'absence de réglage conserve la politique générale d'héritage existante.
- Suite locale complète `manage.py test --parallel 4 --noinput` : 574 tests lancés, 441,580 s ; six ignorés et trois erreurs `PermissionError: [Errno 1] Operation not permitted` lors de l'ouverture de sockets. Tests concernés : ouverture d'un dossier généré, premier démarrage du programme et synchronisation par relais. Cette exécution n'est donc pas annoncée réussie. La CI complète SQLite/SQL Server/Windows doit être lue sur le commit publié.
- `git diff --check` : réussi.

## Limites et suite

Ce lot ferme seulement l'accès depuis le catalogue au rapport déjà livré. Il ne clôt pas les autres écarts Reporting03 ni l'audit des commandes. Les tests P0 des règlements clients continuent dans un lot distinct ; les 427 entrées Commercial existantes servent à la consolidation de Menus05, sans nouvel audit générique. Aucune fusion, aucun déploiement ni donnée de production modifiée.
