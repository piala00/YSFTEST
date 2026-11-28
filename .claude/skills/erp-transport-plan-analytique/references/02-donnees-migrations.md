# 02 — Modèle logique, tables, API et migrations

## Principe de provenance

Conserver deux couches :
- **Faits sources** : billets émis/remboursés, voyage exécuté, colis transporté, consommation de carburant, sortie de pièces, paie validée, charges communes, commission partenaire. Chaque fait a identifiant unique, montant/devises/date d'effet, statut, responsable, agence et document source.
- **Allocations analytiques** : lignes de répartition vérifiables faisant référence au fait ou à la ligne comptable source, avec plans/sections et version de règle. Les rapports sont des vues dérivées, jamais une saisie parallèle de chiffre d'affaires.

## Entités minimales à créer/réutiliser après audit

| Entité | Champs clés | Contraintes |
|---|---|---|
| `analytical_axis` | `id`, `tenant_id`, `code`, `name`, `required_policy`, `enabled` | UNIQUE(tenant_id, code) |
| `analytical_section` | `id`, `axis_id`, `tenant_id`, `code`, `label`, `valid_from`, `valid_to`, `parent_id`, `state` | code stable, historisé, tenant/axe cohérents |
| `vehicle_class_history` | `id`, `vehicle_id`, `fare_class`, `valid_from`, `valid_to`, `approved_by` | exclure les intervalles incompatibles |
| `vehicle_ownership_history` | `vehicle_id`, `partner_id` ou compagnie, `from`, `to` | pas de double propriétaire exclusif non justifié |
| `vehicle_operation_contract` | `vehicle_id`, `partner_id`, `contract_version`, `from`, `to`, `model` | conditions datées, partenaire peut être différent du propriétaire juridique |
| `analytical_rule` | `id`, `event_type`, `account_family`, `condition`, `effective_from`, `effective_to`, `version`, `state` | version immuable après validation |
| `analytical_fact` | `id`, `source_event_id`, `source_document_id`, `journal_line_id`, `amount`, `currency`, `effective_date`, `recognition_state` | un fait logique ne doit pas être créé deux fois |
| `analytical_allocation` | `id`, `fact_id`, `axis_id`, `section_id`, `amount`, `allocation_batch_id`, `rule_version`, `source_role` | section appartient à son axe, contrôle total par vue analytique |
| `allocation_batch` | `id`, `method`, `basis_snapshot`, `effective_period`, `posted_status`, `approved_by` | traçabilité des calculs, arrondi explicite |
| `analytical_correction` | `id`, `original_allocation_id`, `reason`, `new_batch_id`, `actor_id` | rectification sans suppression silencieuse |
| `analytical_reconciliation` | `period`, `entity`, `account_family`, `source_total`, `allocated_total`, `difference`, `status` | écart visible et justifié |

**Attention aux dimensions multiples** : une opération de 100 000 FCFA peut être intégralement étiquetée selon AGC, VEH et GAM — ce n'est pas 300 000 FCFA. Ne pas sommer naïvement `analytical_allocation.amount` sur les dix axes. Employer soit une table **d'affectation complète par fait** (ensembles de dimensions pour chaque ligne de répartition), soit des allocations **par axe et par lot** et imposer le regroupement `axis_id` dans les agrégations. Documenter la méthode retenue.

## Modèle cible recommandé, robuste au double comptage

`analytic_slice(id, fact_id, allocation_group_id, amount, currency, rule_version, valid_state)` représente une **fraction économique unique**. Les relations `analytic_slice_dimension(slice_id, axis_id, section_id, role)` décrivent les dimensions de cette même fraction. Les calculs de rentabilité agrègent `analytic_slice.amount` **une fois par `slice_id`** après filtres dimensionnels, jamais une jointure cartésienne non contrôlée. Plusieurs slices pour un fait : somme des montants = montant attribuable du fait dans la vue choisie ; reliquat explicite si imputation partielle. 

Lorsqu'un même coût commun doit être réparti différemment selon plusieurs vues (agence vs gamme), conserver la **version et le jeu de ventilation** : une projection séparée par `allocation_view` (ex. coût direct, coût complet, simulation budgétaire), pas des lots concurrents additionnés.

## Concurrence et intégrité

- Types financiers `DECIMAL/NUMERIC`, jamais `float`, avec précision adaptée et arrondi par devise.
- Clés et recherches filtrées `tenant_id`/`legal_entity_id` dans tous les services et APIs ; garanties au niveau requête et validation côté serveur.
- `UNIQUE(tenant_id, source_event_id, allocation_view, rule_version, revision)` pour prévenir les doublons logiques ; possibilité de contre-écritures documentées.
- Check transactions : somme des slices d'une vue à la source éligible, y compris éventuelle ligne `NON_AFFECTÉ` **affichée en anomalie**, pas dissimulée.
- Index sur `(tenant_id, effective_date, vehicle_id/trip_id)` ou index de jointure des dimensions selon modèle final.
- Pour `trip`, stockage du type de voyage obligatoire et vérification transactionnelle `trip.fare_class == vehicle_class_at(trip.start_at)` ; les contrôles doivent couvrir l'ensemble de l'intervalle si remplacement de véhicule.
- Table de journal analytique, corrections et règles versionnées `append-only` pour états validés.
- Ne pas figer `partner_id` à partir du propriétaire courant pour des opérations anciennes : calcul en fonction des dates d'effet du contrat applicable, tout en conservant le snapshot utilisé.

## Migrations non destructives

1. Sauvegarder le schéma et identifier les migrations existantes ; ne pas modifier les historiques déjà déployés.
2. Ajouter catalogues/colonnes nullable et nouvelles tables, index puis clés (online si SGBD le permet).
3. Initialiser les sections à partir des agences/véhicules/partenaires réels, avec mapping idempotent ; ne pas fabriquer de codes pour des entités inconnues.
4. Initialiser l'historique Classique/VIP à partir des données fiables seulement ; marquer `A_VERIFIER` lorsqu'une flotte passée ne peut pas être déduite.
5. Backfill par lots avec positions, idempotence, rapport `non_assigne` ; aucune réécriture des documents comptables historiques.
6. Activer lecture en shadow mode, comparer agrégats à la comptabilité et rapports existants ; basculer production après feu vert et seuils définis.
7. Restaurer une projection analytique depuis les sources et les versions de règles ; **ne jamais** restaurer à coups de modifications de caisse/journal sans pièce.
8. Documenter rollback applicatif + comportement en présence des nouvelles tables, et sauvegarde vérifiée avant toute migration.

## APIs indicatives, après audit du stack

- `GET /api/analytical/axes`, `POST /api/analytical/axes` (administration seulement).
- `GET /api/analytical/sections?axis=VEH`, `POST ...`, `PATCH .../close` (date d'effet).
- `POST /api/analytical/rules/validate`, `POST /api/analytical/rules/publish` (séparation des tâches).
- `POST /api/analytical/allocations/preview` (sans mutation), `POST /api/analytical/allocations/approve`.
- `GET /api/analytical/profitability?vehicle_id=...&period=...&view=direct|full`.
- `GET /api/analytical/reconciliation?period=...`, `GET /api/analytical/unassigned`.

Toute API doit vérifier la portée de l'utilisateur, l'appartenance à la compagnie et les permissions fonctionnelles. Les appels de simulation ne déclenchent aucune écriture de production.
