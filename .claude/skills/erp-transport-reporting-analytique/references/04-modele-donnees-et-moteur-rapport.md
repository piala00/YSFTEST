# 04 — Modèle de données, grain et moteur de reporting

Commencer par auditer les modèles réels. N'ajouter des tables que si les objets existants ne peuvent porter ces informations. Noms **illustratifs** : ne pas imposer un schéma unique.

## Entités / champs recommandés

- `tenant/company`, `agency`, `service`, `cash_register`, `vehicle`, `vehicle_class_assignment` (vehicle_id, class, valid_from/to), `trip`, `route`, `route_segment`, `owner`, `vehicle_owner_contract` (vehicle_id, owner_id, valid_from/to, contract_rule_id).
- `source_document` (type, natural_id, tenant, agency, status), `business_event` (event_id UUID unique, source_doc, event_type, occurred_at, service, immutable payload_ref).
- `gl_entry`, `gl_line` (line_id unique, account, debit, credit, currency, accounting_date, status, original_event_id, correction_relation).
- `analytic_axis` (axe); `analytic_section` (section, valid_from/to); `allocation_rule` (version, méthode, validité, périmètre); `analytic_allocation` (allocation_id, gl_line_id, entity_section_ids, amount_signed, allocation_version, event_source_ref, status). Ne pas copier les encaissements comme lignes produit.
- `operational_fact` (trip/boarding/parcel/vehicle-km, event reference, quantities) séparé des montants de ledger.
- `report_definition` (metric id, version, filters, group, source rule); `report_snapshot` (scope, as_of, source cursor, status draft/final, checksum, definition version), `agency_sync_watermark`.
- `owner_settlement_ledger` (contract_id, entitlements, adjustments, holds, payments, opening balance ; linked source) : auxiliaire distinct de résultats analytiques véhicules.

## Architecture logique

`Moteur GL` + `Moteur analytique` + `Faits physiques` → couche de métriques versionnées → vues matérialisées/cache **reproductibles** → APIs filtrées tenant/RBAC → interfaces/exports.

Important : les tableaux matérialisés, cubes ou caches ne sont que des projections dérivées, jamais des sources indépendantes permettant de modifier les montants.

## Invariants

- Un `gl_line_id` n'est ventilé qu'à hauteur du montant éligible ; pour chaque axe concerné somme allocations == valeur GL éligible, ou différence explicitement enregistrée en `non_affecté`.
- Plusieurs axes sur **la même** ligne GL ne signifient pas multiplier la charge par le nombre d'axes. **Ne jamais sommer tous les axes ensemble**.
- Allocation partagée entre véhicules : fractions somme 1 (ou pourcent 100), arrondis résiduels affectés de manière déterministe, conserver les unités monétaires entières et la traçabilité.
- Une agrégation propriétaires se joint sur **propriétaire valable à la date d'imputation** ; la relation actuelle n'est pas suffisante.
- Regroupement de métriques physiques par segments/sièges-km pour éviter le double comptage des passagers sur trajets composés.
- Toutes les requêtes incluent le tenant et les droits d'accès ; les APIs vérifient les filtres, pas uniquement les écrans.
- Les réémissions d'événements et reconstructions de cache ne modifient pas le grand livre ni ne doublent les lignes analytiques.

## Exemple de requête conceptuelle (pseudo-SQL)

```sql
-- Pré-agréger les écritures ventilées : ne pas les joindre directement
-- aux scans ou événements multiples des billets.
WITH vehicle_net AS (
 SELECT company_id, vehicle_id, period_key, metric_type,
        SUM(signed_amount) AS amount
 FROM analytic_fact_normalized
 WHERE company_id = :authorized_company_id
   AND accounting_status IN (:accepted_statuses)
 GROUP BY company_id, vehicle_id, period_key, metric_type
)
SELECT vehicle_id, period_key,
       SUM(CASE WHEN metric_type = 'PRODUCT' THEN amount ELSE 0 END) AS produits,
       SUM(CASE WHEN metric_type = 'COST' THEN amount ELSE 0 END) AS charges
FROM vehicle_net
GROUP BY vehicle_id, period_key;
```

`analytic_fact_normalized` est une **vue conceptuelle** à construire à partir des modèles réellement présents ; le code ci-dessus n'est pas une migration exécutable.
