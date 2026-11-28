# P004.2 — frais d'imprévus et recettes à bord

Codex, 31 octobre 2026. D-002 / Q-001 ; correctif découvert lors de la préparation des échanges, depuis #32. Aucun nouvel audit général.

## Défauts reproduits

Le même frais persisté peut être comptabilisé deux fois depuis deux instances : deux écritures au lieu d'une, confirmé avant correction. Un frais déjà comptabilisé pouvait aussi réécrire son montant à partir du cache. Les frais et recettes à bord acceptaient un départ distant ; une recette pouvait se baser sur un ancien statut. Le POST d'un frais distant pouvait même créer un nouvel imprévu local. Les montants non finis ou fractionnaires ne recevaient pas tous un refus métier avant l'opération.

## Correctif

Relecture et verrouillage du frais existant ; refus s'il est déjà comptabilisé, supprimé ou issu d'une copie miroir. Les opérations relisent/verrouillent le départ et vérifient son propriétaire ainsi que le mode de synchronisation. Le transbordement réutilise ce contrôle commun ; son calcul reste inchangé. Le formulaire refuse un départ distant avant de créer l'imprévu. Les frais respectent le montant entier positif de leur champ existant ; aucun taux ou compte fiscal nouveau n'est imposé.

## Vérifications exécutées

- Dix nouveaux tests : neuf unitaires/HTTP et un concurrent à deux connexions.
- Avant correction : dix tests lancés, huit échecs d'assertion et deux erreurs dans des sous-cas, un ignoré SQLite. Il ne s'agit pas de dix anomalies distinctes ; le test isolant le doublon constate `2 != 1` écritures.
- Après correction : 20 tests ciblés avec les parcours existants de transvasement et d'indemnisation, OK en 3,610 s, un ignoré (concurrence SQL).
- Suite locale complète : 610 tests lancés en 605,792 s, onze ignorés et trois erreurs de sockets `PermissionError: [Errno 1] Operation not permitted` sur les parcours déjà identifiés (dossier généré, démarrage du programme, relais). Cette suite n'est pas annoncée réussie. Le benchmark mensuel fictif s'exécutait parallèlement dans une autre base. CI SQLite/SQL Server/Windows à lire sur le commit publié.
- Panne après publication réelle : rollback de l'écriture et de l'outbox puis reprise du frais persisté ; une seule écriture finale.
- Test HTTP en administrateur sur un départ distant : aucun nouvel imprévu ni décaissement. `git diff --check` réussi.

## Portée

La protection concerne une pièce de frais persistée. Deux formulaires distincts créant deux nouveaux imprévus n'ont pas encore d'identifiant de requête commun ; leur idempotence reste un chantier séparé. Les données historiques ne sont pas réécrites et toutes les manipulations ORM ne sont pas certifiées. Le montant, les écritures et les identités de recette sont fictifs. Aucun déploiement, aucune fusion ni modification de production.
