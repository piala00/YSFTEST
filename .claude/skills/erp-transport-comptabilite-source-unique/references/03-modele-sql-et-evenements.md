# 03 — Modèle technique cible (adapter au schéma réel, ne pas créer de doublons)

## Entités conceptuelles

- `gl_entry(id, company_id, journal_id, accounting_date, status, source_document_type, source_document_id, posted_at, posted_by, reversal_of_id, ...)`
- `gl_line(id, entry_id, account_id, third_party_id, debit, credit, currency, accounting_period_id, ...)`
- `analytic_axis(id, company_id, code, label, ...)`, `analytic_section(id, axis_id, code, valid_from, valid_to, ...)`
- `analytic_allocation(id, company_id, gl_line_id NOT NULL, amount_signed, allocation_version, status, created_at, approved_by, ...)`
- `analytic_allocation_dimension(allocation_id, axis_id, section_id)` (une allocation peut porter plusieurs dimensions ; empêcher doublons de la même dimension).
- `analytic_reconciliation(company_id, period_id, scope_id, gl_eligible, allocated, unallocated, variance, last_check_at, status, ...)`
- `accounting_outbox(event_id, company_id, gl_entry_id, action, event_version, ...)` pour synchronisation, projection et reprise idempotente.
- `analytic_anomaly(id, company_id, source_id, issue_type, detail, severity, resolved_at, ...)`.

Conserver les noms natifs du projet si le schéma existant couvre déjà ces concepts. Éviter table financière analytique éditable sans lien GL. Un index sur `(gl_line_id, allocation_version)` doit garantir que seules les versions actives participent aux totaux.

## Transactions

```
Service: facture/encaissement/etc. → écriture GL brouillard
Comptable/règle automatique autorisée : GL_POSTED, équilibrage + commit
Dans la même transaction DB: événement de publication outbox
Consommateur idempotent: lit GL_POSTED → projections analytiques
Répartition: somme algébrique des allocations = montant source éligible
Publication des états: seulement versions validées et réconciliées
```

L'utilisation d'un journal analytique historique est possible uniquement comme **projection read-model** avec clé étrangère vers GL. Il ne devient jamais un second grand livre autonome.

## Montants, signes et arrondis

- Utiliser `DECIMAL`/`NUMERIC` ou des unités monétaires entières, jamais `float` binaire pour les sommes.
- Définir conventions de signes par nature de compte (produit/charge). Ne pas soustraire une sortie de caisse pour créer arbitrairement une charge analytique.
- Lors d'une ventilation par pourcentage, distribuer les résidus d'arrondi de manière déterministe. P.ex. 100 000 répartis 1/3, 1/3, 1/3 → 33 333, 33 333, 33 334 ; total source préservé.
- Les révisions d'allocation ne réécrivent ni le solde GL ni les allocations historiques sans audit ; utiliser un numéro de version approuvé, une activation de version atomique et contrôle de clôture.

## Autorisations

Seul un rôle comptable habilité / une règle validée peut poster en GL. Les opérateurs métier ne peuvent pas créer directement des lignes analytiques monétaires ; les contrôleurs analytiques peuvent proposer un changement de section, sous autorisation et audit. Les partenaires ont accès en lecture uniquement à leur propre portefeuille à la date pertinente.
