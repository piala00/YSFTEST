# 07 — Offline-first, sécurité, échelles et performance

## Fraîcheur

- Chaque agence rapporte `last_applied_event_id`, `last_sync_at`, nombre d'événements en attente et statut de clôture pour la période.
- Rapports siège ne prétendent **jamais** être complets si une agence du périmètre n'est pas synchronisée ; afficher agence, retard et statut provisoire.
- Une demande d'état ne doit pas exiger une reconnexion permanente pour permettre le travail local de l'agence.
- Réconciliation après réseau et électricité : événements persistés en local, transfert retry idempotent, réordonnancement contrôlé, erreurs en file de supervision.

## Isolation et RBAC

- Filtrer à la source par `tenant/company_id`. Direction/contrôle de gestion : périmètre autorisé ; chef d'agence : agences autorisées ; garage : opérations de maintenance mais pas solde des autres propriétaires ; partenaire : uniquement ses véhicules/contrats/paiements à date ; agent billetterie : sa caisse et opérations de vente autorisées.
- Éviter toute fuite par agrégats `toutes agences` ou erreurs d'API. Tester accès indirect par IDs devinés, exports, drill-down et caches.
- Conserver audit des consultations sensibles, exports, changements de définition de KPI, règles d'affectation et demandes de correction.

## Débits et performances

- Indexer (`tenant_id`, `agency_id`, `vehicle_id`, `accounting_date`, `trip_id`, `owner_contract_id`) selon schéma existant et mesures réelles ; pagination et filtres toujours par serveur pour grands ensembles.
- Pré-agréger par période et grain minimal retenu, invalider/reconstruire les caches après écritures correctives et retours offline, préserver versions de règles.
- Éviter les jointures N:M sur écritures × ventes × scans × voyages. Contrôler cardinalités et doublons par tests.
- Ne jamais utiliser un cache ou une vue matérialisée comme seule preuve du solde à payer au propriétaire ; reprendre le ledger auxiliaire au besoin.

## Qualité et confidentialité

- Masquer les données personnelles des passagers dans les agrégats ; drill-down exposé uniquement aux droits appropriés ; produire agrégats nécessaires plutôt que diffuser toute la base.
- Chiffrement en transit, sauvegardes locales/centrales, restauration testée, piste d'audit, validation comptable des paramètres OHADA.
