# F03.1 — suivi des incidents de colis entre agences

Codex, 31 octobre 2026. Suite de #30 ; ANO-F-001, échanges et scénarios métier déjà livrés en #20. Le lot réutilise les UID, lots `.erpx`, signatures HMAC, journal sortant transactionnel, dépendances, révisions et relais existants.

## Changement

Les déclarations, résolutions, autorisations et paiements d'incidents locaux publient leur suivi. Le rattrapage inclut les incidents antérieurs sans doubler ceux déjà publiés. Deux champs additifs conservent le site et la trace d'origine, avec libellés et identifiants locaux des auteurs associés au site émetteur ; aucun utilisateur local homonyme n'est créé ni désigné comme auteur distant.

Le siège reçoit une copie et rattache l'écriture d'indemnisation reçue séparément ; si cette écriture manque, le suivi payé attend. Une agence d'arrivée reçoit seulement les faits utiles au colis et la référence du paiement : aucune écriture générale distante ne lui est transmise par ce nouveau relais, aucun paiement n'est rejoué. L'import n'appelle aucun service de déclaration, autorisation ou paiement.

Les copies distantes sont en lecture seule dans la fenêtre et dans les trois services de modification, y compris pour un administrateur local. La déclaration reste au site propriétaire du colis, comme auparavant. L'import verrouille le colis avant de créer/lire sa copie et conserve la révision intégrée : une réception plus ancienne ne réécrit pas un suivi plus récent, même si elle attendait le verrou. Les montants non finis, négatifs ou fractionnaires, les constats invalides et les origines incompatibles sont refusés.

## Vérifications exécutées

- Quatorze nouveaux tests : 12 tests de contrat/publication/lecture, une recette de trois bases SQLite distinctes par vrais lots signés, un test d'import concurrent à deux connexions.
- Ciblés finaux : 14 tests en 57,350 s, OK avec un ignoré sous SQLite (concurrence). La recette de trois bases a été réellement exécutée : lot de paiement reçu avant le colis, mise en attente puis reprise, rejeu, relais Douala → siège → Yaoundé ; un incident résolu, deux écritures au siège (apport fictif et une indemnité de 5 000), zéro écriture à Yaoundé, référence de paiement et auteurs préservés.
- Premier passage : une fixture d'événement sans lot et une comparaison textuelle `5000`/`5000.00` ont été corrigées ; il ne s'agissait pas de deux anomalies métier reproduites.
- Panne d'outbox : la résolution est annulée avec la transaction ; la version précédente et son événement restent cohérents.
- Suite locale complète finale : 600 tests lancés en 445,171 s ; dix ignorés et trois erreurs `PermissionError: [Errno 1] Operation not permitted`, sur les mêmes parcours de sockets locaux (dossier généré, démarrage, relais). Cette suite n'est pas annoncée réussie. SQLite/SQL Server/Windows complets à lire sur le commit de CI publié ; le nouveau test concurrent n'est pas annoncé exécuté sous SQLite.
- Migration additive `0019_origine_incidents_colis` : contrôle `makemigrations --check --dry-run`, aucun changement détecté ; `git diff --check` réussi.

## Limites

Ce lot ne clôt pas les échanges des incidents de véhicules, du garage ou des décomptes propriétaires. Le journal et les contrôles de lots existants restent utilisés ; ce n'est pas une certification de tout import concurrent du logiciel. Les anciens récepteurs ne connaissent pas ce nouveau type : les versions des postes doivent être alignées lors d'une intégration future. Un lot HMAC est authentifié, pas chiffré ; le canal de transfert existant reste maîtrisé par la société.

Les scénarios utilisent uniquement des identités, sociétés et montants fictifs. Aucun barème d'indemnisation n'est inventé. PR en brouillon ; aucune fusion, aucun déploiement ni modification de production.
