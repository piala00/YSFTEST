# 10 — Modèle de données, API, sécurité et rôles

## Stratégie de données

Commencer par faire l'inventaire des modèles du dépôt réel. La matrice ci-dessous constitue un **référentiel logique** (pas un SQL DDL plug-and-play). Normaliser les transactions, conserver les événements immuables et produire des vues de lecture/reporting dérivées. Isoler strictement `tenant_id`, `legal_entity_id` et domaines `agency_id` ; même les recherches par identifiants doivent les filtrer. Utiliser des clés étrangères, contraintes métier, transactions atomiques, versions optimistes et index de performance adaptés au SGBD choisi.

## Catalogue des entités minimales

| Domaine | Entités à créer/réutiliser | Clés/champs importants |
|---|---|---|
| Multi-compagnies | `tenant`, `legal_entity`, `agency`, `department`, `service` | identifiants, fiscalité/pays, fuseaux, hiérarchie, statut |
| Identité | `user`, `role`, `permission`, `user_assignment`, `audit_event` | périmètre de droits, MFA privilégié, dates d'effet |
| Tiers | `party`, `customer`, `supplier`, `partner`, `party_address` | rôles, société, confidentialité, consentements si nécessaire |
| Flotte | `vehicle`, `vehicle_ownership_history`, `vehicle_document` | véhicule, propriétaire, capacité, état, date d'effet |
| Transport | `route`, `route_stop`, `trip`, `trip_vehicle_assignment`, `trip_crew_assignment`, `seat_layout`, `trip_seat_entitlement` | tronçons, capacités, quotas, état |
| Billetterie | `reservation`, `ticket`, `ticket_coupon`, `ticket_status_history`, `boarding_scan`, `ticket_refund` | identifiants uniques, dates, paiements, signature QR |
| Messagerie | `shipment`, `parcel`, `shipment_leg`, `parcel_scan`, `parcel_handover`, `delivery_proof`, `cargo_claim` | tracking, custody, véhicule par étape |
| Garage | `maintenance_order`, `maintenance_task`, `maintenance_part_usage`, `odometer_reading` | pièces, interventions, validation, kilomètres |
| Achats/stocks | `purchase_request`, `purchase_order`, `goods_receipt`, `supplier_invoice`, `inventory_movement`, `inventory_count` | quantité, magasin, coût, véhicule/OR |
| Carburant | `fuel_issue`, `fuel_purchase`, `fuel_tank`, `fuel_stock_movement` | litres, km, fournisseur, paiement, véhicule/voyage |
| RH/paie | `employee`, `employment_contract`, `shift`, `attendance`, `leave_request`, `payroll_period`, `payslip`, `payroll_item`, `payroll_payment` | agence, période, rubriques, montants, statut |
| Caisse | `cash_register`, `cash_session`, `payment`, `cash_movement`, `cash_remittance`, `cash_transfer`, `bank_reconciliation` | montant, devise, sens, tiers, justificatif |
| Comptabilité | `fiscal_period`, `account`, `journal`, `posting_rule`, `journal_entry`, `journal_line`, `tax_rule` | compte, débit/crédit, exercice, source, version |
| Analytique | `cost_center`, `allocation_rule`, `analytical_entry`, `allocation_batch`, `vehicle_profitability_snapshot` | dimensions, provenance, clé, méthode |
| Partenaires | `partner_contract`, `partner_contract_version`, `partner_statement`, `partner_statement_line`, `partner_payment` | assiette, dépenses, droits, advances, solde |
| Synchronisation | `outbox_event`, `inbox_event`, `sync_cursor`, `sync_attempt`, `sync_conflict` | source, idempotence, causalité, état |
| Supervision | `agency_daily_close`, `service_daily_close`, `trip_close`, `report_snapshot`, `reconciliation_case` | signature, complet/provisoire, anomalie |

## Contraintes relationnelles prioritaires

- `UNIQUE(tenant_id, ticket_number)` ou clé métier équivalente ; aucun billet actif pour le même droit de siège/tronçon exclu par invariant stock de places.
- `UNIQUE(tenant_id, producer_id, event_id)` dans chaque inbox ; dans comptabilité, `UNIQUE(source_event_id, posting_rule_version, posting_kind)` sauf version/correction explicite.
- `CHECK(amount >= 0)` si `direction` stocke le sens, `CHECK(quantity > 0)` pour sortie/entrée unitaire normale ; corrections comme mouvements inverses.
- Clé étrangère `journal_line.entry_id` et validation `SUM(debits)=SUM(credits)` par transaction métier, pas simple check de ligne.
- Entité `trip_vehicle_assignment` à intervalles valides sans chevauchement incompatible pour un même véhicule, idem contrat propriétaire si exclusif.
- `ticket_status_history` append-only et transition validée ; scans enregistrement atomique et contrainte d'unicité sur la consommation effective par coupon/segment.
- Mouvements financiers et de stock append-only ; aucune mutation directement dans des projections de solde.
- Plusieurs devises : conserver montant en devise source, devise comptable, taux appliqué, type/date de taux et origine ; ne pas mélanger FCFA et autres sans conversion explicite.

## Schémas type des commandes et événements

Exemple conceptuel API (noms indicatifs, adaptés à l'existant) :

```http
POST /api/v1/tickets
Idempotency-Key: c7f...unique-per-command
X-Agency-ID: agency-bertoua

{
  "trip_id": "...", "boarding_stop_id": "...", "alighting_stop_id": "...",
  "seat_id": "...", "fare_quote_id": "...", "payment_request": {"method": "cash"}
}
```

La requête est **authentifiée**, agence permise vérifiée côté serveur, tarif recalculé/vérifié, siège verrouillé sous transaction locale, document/événement durable ; retour identifiant et statut réel du paiement. Le client web n'a pas autorité pour fournir un montant comptable définitif arbitraire. `Idempotency-Key` empêche les doubles clics/réémissions.

```json
{
  "event_id": "UUID",
  "event_type": "FuelDispensed",
  "schema_version": 1,
  "tenant_id": "UUID",
  "legal_entity_id": "UUID",
  "agency_id": "UUID",
  "actor_id": "UUID",
  "aggregate_type": "FuelIssue",
  "aggregate_id": "UUID",
  "occurred_at_utc": "2026-10-25T14:07:00Z",
  "effective_business_date": "2026-10-25",
  "correlation_id": "UUID",
  "payload": {
    "vehicle_id": "UUID",
    "trip_id": "UUID-or-null",
    "liters": "60.000",
    "unit_cost_fcfa": "decimal-as-string",
    "source_document_id": "UUID"
  }
}
```

C'est un **exemple de structure**, non une donnée réelle ni un format contractuel définitif. Versionner événements/API et prévoir migrations de consommateurs anciens.

## Matrice de rôles (par défaut à configurer)

Légende : `E` enregistrer son domaine, `V` consulter son domaine, `A` approuver/contrôler, `G` gérer globalement, `–` aucun accès. Chaque droit est ensuite restreint par compagnie, société, agence, service et éventuellement caisse/vehicule.

| Rôle | Billets | Colis | Voyages | Garage | Paie | Caisse | Compta | Partenaire |
|---|---|---|---|---|---|---|---|---|
| Guichetier | E | – | V | – | – | E sa caisse | – | – |
| Contrôleur | V+scan | V manifeste | V | – | – | – | – | – |
| Agent messagerie | – | E | V chargement | – | – | E sa caisse si habilité | – | – |
| Chef exploitation | V | V | E/A | V état | V disponibilité | – | V analytique restreint | – |
| Mécanicien | – | – | V affectations | E OR | – | – | – | – |
| Magasinier | – | – | – | E pièces et stocks | – | – | – | – |
| RH / gestionnaire paie | – | – | V équipages | – | E/A selon séparation | – | V journaux concernés | – |
| Caissier / trésorier | V réglé | V réglé | – | V factures approuvées | V ordres paie | E/A | V mouvements | V ordres paiement |
| Comptable | V | V | V | V | V écritures | V rapprochement | E/A | V décomptes |
| Gestionnaire partenaires | V agrégé | V agrégé | V | V coûts | – | V règlements | V auxiliaire | E/A |
| Chef agence | A selon délégation | A | A | V | V présence non paie | A | V situation agence | V situation locale |
| Direction | G lecture | G lecture | G lecture | G lecture | Synthèse autorisée | G lecture | G lecture | G lecture |
| Partenaire externe | – | – | V uniquement ses véhicules | V coûts éligibles | – | V ses règlements | V son compte | V ses relevés |

Les droits d'autoriser un remboursement, valider une paie, approuver un décompte et émettre un virement doivent pouvoir être séparés de la saisie. `admin IT` n'a pas automatiquement le droit de lire les bulletins de salaires ni d'effectuer des paiements.

## Politique d'autorisation

Implémenter RBAC **plus** contrôle de périmètre (ABAC) : `user_id`, `tenant_id`, `legal_entity_id`, `allowed_agency_ids`, rôle sur service, droit opérationnel, seuil financier, relation de propriété et période. Contrôles côté serveur y compris exports, impressions, webhooks et tâches arrière-plan. Protéger contre les IDOR (accès en modifiant l'ID dans l'URL). Journaliser les tentatives refusées.

## Audit et versions

`audit_event` immuable : horodatage, utilisateur et terminal, action, raison, objet, version avant/après (données sensibles minimisées), scope, adresse/trace réseau si licite. Les documents RH et personnels exigent accès restreint et rétention propre au pays. Indiquer au tableau de bord les informations cache/dérivées avec date de fraîcheur.
