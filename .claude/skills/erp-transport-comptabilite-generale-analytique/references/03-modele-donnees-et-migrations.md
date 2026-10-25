# 03 — Modèle conceptuel / contraintes et migrations

## Tables candidates (adapter au schéma EXISTANT)

Noms ci-dessous conceptuels : **ne pas créer une seconde table si une équivalente existe**.

| Domaine | Tables / champs essentiels |
|---|---|
| Référentiel | `legal_entity(id)`, `agency(id, entity_id)`, `service(id)`, `vehicle(id, code, plate)`, `owner(id, type=COMPANY/PARTNER)` |
| Classe | `vehicle_service_history(vehicle_id, class=CLASSIQUE/VIP, effective_from, effective_to)` ; contraintes anti-chevauchement |
| Contrat | `vehicle_operating_contract(id, vehicle_id, owner_id, start_at, end_at, terms_version, company_role, allocation_rule_id)` |
| Exploitation | `trip(id, vehicle_id, departure_at, operator_agency_id, class, route_id)` ; liaison ventes/courrier/bagage/garage/charge avec véhicules réels |
| Comptabilité générale | `gl_journal`, `gl_entry(id, source_event_id, status, period_id, entity_id)`, `gl_line(id, entry_id, account_id, debit, credit, currency, source_ref)` |
| Compta analytique | `analytic_posting(id, gl_line_id, vehicle_id, owner_id_snapshot, contract_id_snapshot, allocation_rule_version, amount, type, effective_at)` ou lien vers éventuel ledger analytique déjà présent |
| Ventilation | `analytic_allocation(id, source_line_id, vehicle_id, amount, allocation_method, denominator, numerator, reason, version)` ; somme allouée égale à éligible si ventilation complète |
| Compte partenaire | `partner_settlement(id, owner_id, period_start, period_end, status, contract_version)`, `partner_settlement_line(id, settlement_id, vehicle_id, basis, credit, debit, source_ref)`, `partner_payment(id, owner_id, amount, payment_event_id)` |
| Audit/sync | `outbox_event(id, aggregate_id, type, payload, origin_agency_id, event_version)`, `sync_receipt(origin_agency_id, event_id unique)`, `change_audit` |

## Contraintes / relations

- `company_id`/`tenant_id` partout où cela est nécessaire ; aucun accès inter-compagnies dans les requêtes.
- `gl_entry`: contraindre somme débits = crédits à la validation, référence document source, période ouverte, pas de suppression d'écriture validée.
- L'unicité `origin_agency_id + source_event_id + accounting_policy_version` protège contre relecture du même événement, tenant compte d'une correction sous événement distinct.
- `analytic_posting`: une ligne source peut être découpée entre plusieurs véhicules, MAIS la **somme des parties** est égale au montant affectable ; aucune duplication par les 10 dimensions transversales.
- `owner_id_snapshot` pour requêtes rapides **plus FK contrat daté** pour preuve ; résoudre le propriétaire d'après l'historique à la date de prestation, non d'après la fiche actuelle.
- Si contrat devient effectif pendant un voyage, règle explicite de répartition ou bascule à un instant métier défini ; rejet sinon et contrôle manuel.
- Ne pas imposer `vehicle_id NOT NULL` à toutes les écritures générales ; les frais communs et actifs non liés à un bus existent.
- Stocker le rapport d'agence payeuse et celui d'exploitation indépendamment ; `cashbox_id` n'est ni `service_id` ni `vehicle_id`.
- Support éventuel de copropriété : table de quote-part propriétaire datée avec somme des parts = 100 % si requis par le métier ; ne pas créer cette complexité sans constat de besoin ou architecture adaptée.

## Exemples de requêtes (pseudocode, pas SQL prêt à exécuter)

```sql
-- Par véhicule et période : utiliser les lignes ANALYTIQUES et leurs parts,
-- pas les montants de billets bruts cumulés puis doublés avec la compta générale.
SELECT vehicle_id,
  SUM(CASE WHEN direction='PRODUCT' THEN amount ELSE 0 END) AS products,
  SUM(CASE WHEN direction='COST' THEN amount ELSE 0 END) AS costs
FROM analytic_posting
WHERE effective_at >= :debut AND effective_at < :fin
  AND tenant_id = :tenant_id AND status = 'POSTED'
GROUP BY vehicle_id;
```

```sql
-- Par propriétaire : période et contrat au moment des faits.
SELECT owner_id_snapshot, vehicle_id,
       SUM(product_amount) AS products, SUM(cost_amount) AS costs
FROM vehicle_result_lines
WHERE effective_at >= :debut AND effective_at < :fin
  AND tenant_id = :tenant_id
GROUP BY owner_id_snapshot, vehicle_id;
```

Les noms `direction` et `vehicle_result_lines` sont fictifs ; adapter à l'ORM réel. Rapports partenaires **ne pas confondre** `owner_id_snapshot` des coûts et l'attribution des droits contractuels après calcul.

## Migration

1. Inventorier schéma et volumes, identifier équivalents, contraintes, index et statuts.
2. Sauvegarde + test de restauration, environnement de recette avec copies anonymisées.
3. Migrations additives, avec backfill traçable depuis documents sources et dates contractuelles ; sans montant inventé.
4. Aucune correction implicite d'écriture générale validée ; constituer file d'anomalies pour imputation manquante.
5. Validation des totaux GL avant/après migration, rapprochement véhicule et partenaires, test redéploiement/rollback.
6. Déployer progressivement sur une agence puis étendre à toutes, monitoring des sync.
