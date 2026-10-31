# P004 — sûreté des règlements clients

Codex, 31 octobre 2026. Exigences D-002, Q-001 et B-002 (U5). Suite indépendante des documents #28 et de Reporting03.1 #29 ; aucune reprise de l'audit général.

## Défauts reproduits et correctif

Un ancien objet de reçu pouvait enregistrer une seconde écriture : test exécuté avant correction, résultat `2 != 1`. Un reçu déjà comptabilisé pouvait aussi être réécrit depuis un montant en mémoire. Les contrôles d'imputation se fiaient aux montants et au tiers d'instances fournies, au lieu de relire systématiquement le reçu et la facture. Un reçu supprimé pouvait être recréé. La copie marquée miroir provoquait une erreur technique d'alias plutôt qu'un refus métier ; ce cas n'est pas présenté comme une écriture en production reproduite.

Le service relit et verrouille désormais les reçus persistés et les factures sous transaction, refuse un nouvel enregistrement déjà comptabilisé ou repris, et refuse les copies miroir et les objets supprimés. Les factures sont verrouillées par identifiant pour garder un ordre commun ; l'imputation FIFO conserve son ordre métier. Le rattachement réutilise le reçu existant sans second encaissement. Les parcours zéro/une/plusieurs factures, l'attente et les acomptes existants sont conservés.

## Tests réellement exécutés

- Douze nouveaux tests ciblés. Avant correction : sept échecs d'assertion, deux erreurs dans les sous-cas miroir, trois tests de concurrence ignorés sous SQLite. Ces nombres ne désignent pas douze anomalies distinctes. Le cas de panne/publication déjà réussi est conservé comme non-régression.
- Test isolé du double encaissement avant correction : deux écritures pour le même reçu, échec confirmé.
- Après correction, nouveaux tests et parcours existants : 53 tests réussis en 24,469 s, trois ignorés (concurrence SQL).
- Régressions Commercial et Comptabilité : 175 tests réussis en 88,474 s, sept ignorés (tests de concurrence SQL de ces modules).
- Suite complète locale : 586 tests lancés en 371,555 s, neuf ignorés et trois erreurs de sockets `PermissionError: [Errno 1] Operation not permitted`, sur les mêmes parcours de dossier généré, premier démarrage et relais. Cette suite n'est pas annoncée réussie. La CI du commit publié doit compléter SQLite, SQL Server et Windows.
- Trois recettes concurrentes utilisent deux connexions réelles : double encaissement du même reçu, un reçu visant deux factures au-delà de son disponible, deux reçus visant une même facture au-delà du reste dû. Elles ne sont pas annoncées exécutées sous SQLite.

## Portée

La recette utilise uniquement des sociétés et montants fictifs. Le verrouillage est celui du service ; ce lot ne certifie ni toutes les écritures directes de modèles, ni les imports, ni toute la concurrence des acomptes et transformations. La protection d'un même reçu persisté n'est pas une garantie d'idempotence entre deux nouveaux formulaires distincts sans identifiant commun.

Résultats CI, SHA et périmètre Windows à publier dans la PR et le tableau d'avancement. Aucune fusion, aucun déploiement ni donnée de production modifiée.
