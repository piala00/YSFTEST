# 05 — Données, APIs, sécurité, fonctionnement multi-agences

## Tables / projections minimales à cartographier (adapter au code existant)
`parties`, `party_roles`, `owners`, `suppliers`, `employees`, `owner_vehicle_contracts`, `contract_versions`, `owner_fixed_due_schedule`, `owner_variable_settlements`, `owner_advances`, `owner_withdrawal_requests`, `owner_payouts`, `owner_account_gl_links`, `general_journal_lines`, `analytic_allocations`, `audit_log`.

Ajouter contraintes d'unicité de référence externe, transactions, idempotency keys, périodes d'effet, absence de contrats actifs incompatibles pour un même véhicule (selon règles métier) et validation des règles de paiement. Ne jamais écrire directement le solde propriétaire comme champ libre modifiable : **recalculer depuis le sous-livre GA**, avec projections matérialisées régénérables.

## Endpoints illustratifs, non imposés
- `GET /owners/{id}/vehicles?at=...`
- `GET /owners/{id}/statement?from=...&to=...`
- `POST /owner-contracts` (validation + approbation et version)
- `POST /owners/{id}/settlements/prepare` ; `POST /.../approve` (séparation des rôles)
- `POST /owner-withdrawal-requests` ; `POST /.../approve` ; `POST /.../pay` (trésorerie, GA, idempotence)
- `GET /owners/{id}/reconciliation` (balances auxiliaires VS éligibilité analytique)

## Autorisations
Propriétaire : voit **seulement** ses contrats, véhicules et états ; ne peut éditer montant fixe, variable, statut GL ou autoriser un retrait. Comptable : valide comptabilisation ; trésorier : exécute paiements autorisés ; responsable : approuve selon seuil ; auditeur : lecture. Le cumul approbateur/payeur doit respecter une séparation des fonctions configurable.

## Hors connexion et paiements
Les ventes, garage et opérations peuvent être saisis localement selon leur autorité, mais un retrait propriétaire de fonds partagés ne doit pas être autorisé en parallèle depuis des agences non synchronisées sur la foi de soldes anciens. Exiger autorité de paiement unique en ligne, ou allocation préalable de plafonds exclusifs réservés et sécurisés ; sinon mettre la demande en `PENDING_CENTRAL_APPROVAL`. Toute demande/paiement possède un ID global, clé idempotence, horodatage et trace d'audit. Les historiques corrigés sont rejoués de manière traçable.
