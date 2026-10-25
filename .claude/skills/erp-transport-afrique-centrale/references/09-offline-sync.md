# 09 — Architecture Offline-First, stockage local, remontée centrale et pannes

## Topologie

Chaque agence a serveur local durable, API LAN et base transactionnelle (PostgreSQL recommandé à étudier selon l'existant). Les terminaux guichet, colis, garage, caisse et contrôleurs communiquent en réseau local. Le siège dispose d'un serveur central et de vues transverses. Des postes mobiles peuvent fonctionner en mode limité avec politique dédiée ; une tablette seule ne remplace pas automatiquement le serveur de validation d'embarquement. Tous les flux WAN via HTTPS mutuellement authentifié ou VPN maîtrisé, certificats et rotation de clés.

**Attention :** le local 24 h/24 nécessite UPS, sauvegardes, réseau local, procédure d'arrêt propre, alimentation redondante et supervision matérielle. Ne jamais promettre que l'agence poursuit l'exploitation si tous ses équipements sont sans énergie.

## Cycle de synchronisation fiable

1. Transaction métier locale : modification tables source + insertion ligne dans `outbox_event` **dans la même transaction**.
2. Worker lit événements non accusés avec limites de lot et retries, construit messages signés/authentifiés, priorise ordre par agrégat.
3. Serveur central reçoit, authentifie `tenant+agency`, valide schéma, droits et dépendances ; inscrit `inbox_event(event_id,producer)` unique ; applique ou met en attente causalité.
4. Retourne ACK par événement ; agence marque confirmé ; pas de suppression précipitée des événements non archivés.
5. Flux descendant idem pour tarifs, référentiels, contrats et quotas avec version/date d'effet ; éviter qu'un paramètre change rétroactivement une pièce déjà validée.
6. Reconnecter : rattrapage incrémental par curseur et/ou séquence logique (pas seulement horodatage d'horloge locale), puis vérification comptes et hashes si pertinent.
7. Doubles transmissions → même résultat métier. Événements incompatibles → file de quarantaine et résolution par utilisateur habilité.

## Résolution de conflits

| Donnée | Autorité | Comportement hors ligne |
|---|---|---|
| Billet payé local | Agence émettrice + quota autorisé | Vente locale et sync idempotente |
| Capacité de voyage | Gestionnaire de sièges/quotas | Quota exclusif préalloué, jamais global concurrent |
| Scan embarquement | Contrôleur/serveur maître du voyage | Validation atomique locale dans même réseau |
| Prix/plan tarifaire | Siège ou instance habilitée | Snapshot versionné offline, ne pas retarifer le passé |
| Propriété/contrat | Gestionnaire siège | Appliquer versions approuvées avec dates d'effet ; pas d'édition concurrente libre |
| Dépense et caisse | Agence/acteur mandaté | Événements locaux ; corrections documentées |
| Paie | RH/finance habilitées | Calcul local éventuel ; **validation finale unique**, éviter doubles règlements |
| Écriture GL | Moteur comptable autoritatif | Source validée → unique posting ; consolidation sans réplication libre des écritures |
| Décompte partenaire | Responsable comptes partenaires | Publication/approbation autoritaire et versions immuables |

Ne jamais appliquer « last write wins » sur soldes, argent, sièges, contrat, stock ou kilométrage. Une divergence exige compensations ou rapprochement traçable. Les soldes sont des **projections des mouvements**, non des valeurs répliquées modifiables.

## Compteurs et identifiants

Utiliser UUIDv7 si disponible ou UUIDv4 globalement unique pour identités techniques. Documents imprimés : séries uniques par espace (`TENANT/SOCIETE/AGENCE/TYPE/ANNEE/COMPTEUR_LOCAL`), plages réservées si nécessaire, contrôle de collisions au siège. L'heure serveur locale n'est pas une autorité universelle ; stocker UTC, fuseau agence, date d'activité (qui peut dépasser minuit) et date comptable.

## Synchronisation et conformité financière

- Une vente payée offline est légalement/financièrement enregistrée dans l'agence dans les limites autorisées ; le siège la marque `non_sync` et ne peut inventer des chiffres complets.
- Écriture issue d'un événement rapprochée par clé stable ; validation et période comptable déterminées par les règles du siège ou de l'entité, pas par réception réseau.
- Avance entre agences non encore confirmée : fonds `en transit`, jamais simultanément dans deux caisses.
- Colis en transit : événement de scan peut arriver avant création de shipment ; file d'attente de dépendance puis rapprochement.
- Toute agence doit pouvoir reconstituer ses rapports de la journée même sans siège ; rapport global siège affiche taux de couverture des agences.

## Pannes et sécurité

Coupures WAN, coupure secteur, panne serveur local, corruption disque, changement d'IP, appareil perdu, vol de jeton, retard NTP, message dupliqué, message hors ordre, migration schema partielle, perte d'ACK, restauration snapshot ancienne. Simuler ces scénarios. Sauvegarder bases et clés séparément selon politique, exécuter des exercices de restauration, journaliser RPO/RTO **comme objectifs à négocier**, non performances garanties. Se prémunir contre la restauration de sauvegarde qui réémet des anciennes opérations : registre central d'`event_id` et stratégie de recovery d'identité des agences.

## Monitoring

Tableau de bord : agence, dernière connexion, dernier événement produit/reçu, backlog, taux d'échec, âge de l'événement le plus ancien, erreurs d'intégrité, stockage disque, sauvegarde, horloge, version de logiciel, alertes d'inventaire sièges, degré de complétude comptable. Ne pas masquer une agence offline derrière un indicateur « tout synchronisé ».
