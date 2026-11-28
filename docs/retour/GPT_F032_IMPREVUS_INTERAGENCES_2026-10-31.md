# F03.2 — imprévus de voyage, frais et port dû entre agences

Codex, 31 octobre 2026. Suite de #33 ; ANO-F-001 / ANO-F-002. Réutilisation du calcul local de transvasement déjà livré ; aucune reprise de l'analyse TR-01.

## Anomalie reproduite

Sur trois bases SQLite séparées et de vrais lots signés, un colis de 2 500 FCFA en port dû est transvasé à 40 % vers un véhicule de secours. L'agence d'arrivée ne recevait pas l'imprévu : elle imputait les 2 500 au véhicule initial. Le calcul local attendait 1 500 sur l'initial et 1 000 sur le secours. Le total encaissé était correct ; la ventilation analytique était erronée. La recette avant correction a réellement échoué et son résultat JSON a été conservé hors dépôt, sur données fictives.

## Changement

Nouveau contrat de suivi pour les imprévus, avec UID, départ, secours, pourcentage, auteur et références GL. Les frais sont transmis comme une photographie d'origine, pas comme de nouvelles lignes locales à payer. Le siège attend les écritures manquantes avant de lier le suivi ; une agence conserve leurs références sans recréer les opérations. Les destinations restent limitées aux agences concernées par le départ.

Les révisions sont protégées sous verrou du départ. La création du suivi et de ses événements est atomique, y compris hors du service financier ; les copies miroir ne publient pas dans le journal de saisie. Les données reçues restent en lecture seule et les auteurs ne deviennent pas des utilisateurs locaux homonymes. Migration additive 0020, sans régénération des UID existants.

La livraison réutilise exactement le calcul de port dû existant, grâce à l'imprévu reçu. Aucun nouveau moteur comptable ni nouvelle règle de répartition n'est ajouté.

## Tests exécutés

- Recette de reproduction avant/après, trois bases distinctes : avant zéro imprévu reçu et 2 500 au véhicule initial ; après un imprévu reçu et 1 500/1 000, total 2 500 inchangé.
- Onze nouveaux tests permanents : neuf contrats/publication/lecture, une recette sur trois bases SQLite par lots signés, un concurrent à deux connexions.
- Ciblés avec les parcours existants : 26 tests OK en 68,905 s, deux ignorés sous SQLite (nouveau concurrent et concurrent des frais #33).
- Recette permanente : paiement d'un dépannage fictif de 1 000 au départ, livraison distante de 2 500 répartie 1 500/1 000, rejeux des lots et de la livraison ; une écriture à destination, trois au siège (apport, dépannage, livraison), aucun nouveau frais local chez les destinataires. Les frais transmis conservent leurs références.
- Panne après publication réelle hors service : suivi et outbox annulés ensemble. Dépendances absentes, mauvaise origine, frais invalides, révision ancienne et fenêtre distante vérifiés.
- Suite locale complète : 621 tests en 580,896 s, douze ignorés et trois erreurs de sockets `PermissionError: [Errno 1] Operation not permitted`, sur les mêmes parcours de dossier généré, démarrage et relais. Cette suite n'est pas annoncée réussie ; CI complète SQLite/SQL Server/Windows à lire au commit publié. Le concurrent nouveau n'est pas annoncé exécuté sous SQLite.
- `makemigrations --check --dry-run` sans changement et `git diff --check` réussis.

## Limites

Les faits nécessaires doivent avoir été reçus ; le fonctionnement hors ligne ne garantit pas une connaissance immédiate des événements distants. Les versions des postes doivent être alignées. Ce correctif ne réécrit pas les ventilations déjà validées ; une éventuelle correction d'historique nécessite un traitement comptable distinct et autorisé. Le chantier garage/décomptes et la certification de toutes les opérations ORM restent ouverts.

Sociétés, clés d'échange et montants de recette fictifs. Aucune fusion, aucun déploiement ni donnée de production modifiée.
