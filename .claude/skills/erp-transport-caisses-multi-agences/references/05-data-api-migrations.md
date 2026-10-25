# 05 — Modèle de données, API, invariants et migration

**Schéma conceptuel à adapter** après analyse du dépôt. N'introduire ni tables ni endpoints en doublon s'ils existent. Les noms sont indicatifs, à mettre en correspondance avec la nomenclature du projet.

## Entités proposées

| Entité | Champs essentiels | Contraintes |
|---|---|---|
| `cashboxes` | id, tenant_id, legal_entity_id, agency_id, code, name, currency, status, purpose, valid_from/to | unique(tenant, legal_entity, agency, code) ; statut et historique |
| `cashbox_assignments` | id, cashbox_id, employee_id, role, valid_from/to, assigned_by | contrôle dates et permissions |
| `cash_sessions` | id, cashbox_id, cashier_id, opened_at, opening_amount, closed_at, counted_amount, approved_by, status | verrouillage de la clôture, unicité sessions selon politique |
| `cash_movements` | id UUID, cashbox_id, session_id, source_event_id, source_doc_type/id, movement_type, amount, currency, occurred_at, operator_id, service_id, agency_id, transfer_id, status | montants positifs + sens explicite, source immuable, FK, idempotence par événement/type |
| `payment_accounts` | id, tenant_id, legal_entity_id, agency_id nullable, account_type BANK/MM/CARD, provider, currency, status | pas de confusion avec espèce physique |
| `financial_payments` | id UUID, source_doc_id, payment_method, cashbox_id nullable, payment_account_id nullable, cashier_id, amount, paid_at, status, idempotency_key | montant positif ; espèce => cashbox ; électronique => compte correspondant ; validations |
| `cash_transfers` | id UUID, from_cashbox_id, to_cashbox_id nullable, destination_bank/account_id nullable, requested_amount, status, initiated_at, sent_at, received_at, initiator/receiver, idempotency_key | transfert entre comptes autorisés de même entité ou interagence prévu ; statut en transit |
| `cash_counts` | id UUID, cash_session_id, counted_at, counted_by, counted_amount, reason, approved_by | écart calculé vs solde livre, contrôle indépendant |
| `cash_closures` | id UUID, agency_id, business_date, cashbox_id nullable, total_*, status, signed_by, sync_watermark, snapshot_hash | historiser éditions / corrections, statut provisoire si sync retardée |
| `audit_events/outbox/inbox` | event_id, origin_node, transaction_id, payload_hash, occurred_at, applied_at, status | unique(event_id), rejouabilité sûre |

Conserver `source_service_id`, `operating_vehicle_id`, `trip_id`, `fare_class`, `partner_contract_id` selon contexte, **sans imposer un véhicule** aux dépenses d'agence générales.

### Exemples d'API (adapter au projet)

- `GET /agencies/{agency_id}/cashboxes` (droits et état).
- `POST /agencies/{agency_id}/cashboxes` (administrateur/gestion autorisée).
- `POST /cashboxes/{id}/sessions/open` et `/close` (transactionnelles).
- `POST /payments` / `POST /disbursements` (événements métier autorisés ; `Idempotency-Key`).
- `POST /cash-transfers` puis `POST /cash-transfers/{id}/confirm-receipt` (contrôles inter-caisses).
- `GET /reports/agencies/{id}/daily?date=YYYY-MM-DD&cashbox_id=all|uuid`.
- `GET /reports/cashboxes/{id}/daily?date=YYYY-MM-DD`.

Protéger la portée tenant/société/agence côté API et requête SQL. Ne jamais permettre qu'un client fournisse seul un `cashbox_id` d'une autre agence. Ne pas croire un total fourni par le navigateur : le serveur recalcule les montants.

## Migration non destructive

1. Inventorier tables de caisse historiques, mouvements, paiements, états, postes ; préparer correspondances de noms et sauvegarde restaurable.
2. Créer/ajouter l'entité caisse si absente ; définir pour chaque agence existante **une caisse héritée par défaut** sans réécrire l'historique original ; tracer la provenance des données migrées.
3. Rattacher les anciens paiements en espèces à leur caisse historique en fonction des données réelles ; **signaler comme non résolu** tout rattachement ambigu au lieu d'inventer une caisse.
4. Ajouter les contraintes progressivement : d'abord nullable/observabilité, backfill vérifié, puis contrainte stricte uniquement sur les nouveaux mouvements, et enforcement complet lorsque les anciens sont corrigés.
5. Les nouveaux mouvements exigent des identifiants idempotents, associés au document source. Les doubles paiements détectés sont à résoudre manuellement avec pièces et écritures compensatoires.
6. Proposer un chemin de retour contrôlé et tests de restauration. **Ne jamais vider ou renuméroter silencieusement la trésorerie historique**.

## Atomicité / concurrence

- Transaction base : validation du montant/droits + mouvement + écritures sous-ledger + outbox, dans une transaction, en verrouillant les soldes/versions concernés.
- Concurrence en caisses locales : version ou verrou sur session/solde et `unique(tenant, idempotency_key)`.
- Transfert : source et réception comme événements distincts idempotents ; statut en transit, sans argent « magique ».
- Le calcul du solde historique doit pouvoir être reconstruit à partir du journal des mouvements et des rapprochements, sans confiance exclusive dans un simple champ de solde mutable.
