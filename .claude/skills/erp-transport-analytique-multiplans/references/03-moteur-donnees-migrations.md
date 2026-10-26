# Moteur analytique multiaxes et migration sûre

## Proposition cible, à adapter après audit ORM/SQL

- `PlanAnalytique` : `id`, `code`, `nom`, `actif`, `rang`, `nature`, `societe_id`, `parent_ou_hierarchie` si besoin.
- `SectionAnalytique` : `id`, `plan_id` normalisé, `code`, `intitule`, `actif`, validité temporelle, relation métier facultative (gare, véhicule, propriétaire, voyage…), avec conservation de l'ancien champ `plan` et ses codes pendant la migration.
- `VentilationAnalytique` : `uid`, `ligne_ecriture_id` FK obligatoire PROTECT vers `LigneEcriture`, `section_id` FK PROTECT, `montant_absolu` Decimal(18,2) positif, signe déduit de la ligne GL, `regle_id`, `regle_version`, `date_effet`, `source`, `created_at`, `created_by`, `site_origine`, identifiant stable/idempotent. Version et état de correction, *pas* de montant hors GL.
- `RegleImputation` : hiérarchie de règles pour les sources opérationnelles (billets, colis, maintenance, paie, achats, partenaires); priorité; dates de validité; affectations calculables et contrôlables.
- `CleRepartition` : base mesurable (kilomètre, voyage, sièges-kilomètres, coût réel…), justification, approbation, période, version. `VentilationRepartition` si nécessaire, dans la limite de la ligne GL.
- `PositionAnalytique` / vues SQL: agrégats matérialisables, reconstruisibles à partir des ventilations et écritures GL, **jamais source de vérité**.

Une même ligne générale de 100 000 FCFA peut être ventilée à 100 % sur `AGC:Bertoua` et 100 % sur `VEH:BUS-001` : total société = **100 000**, pas 200 000. Si on répartit sur deux véhicules au même plan VEH (60 000 + 40 000), la somme de leurs imputations VEH est 100 000. En revanche, il est interdit de sommer sans nuance « AGC + VEH ».

## Invariants techniques

- Ventilation monétaire dérivée seulement de ligne d'écriture *validée*. Si une écriture redevient brouillard, invalider les états certifiés ou bloquer la modification; corriger par contrepassation traçable.
- Pour chaque `(ligne_ecriture, plan)` : `somme(montant_absolu) <= valeur_absolue_autorisée_ligne` à la précision monétaire; contrôler verrou/transac contre concurrence, et fournir résiduel non affecté.
- Vérifier `(section.plan_id == ventilation.plan)` si plan dupliqué dans la ventilation; préférer référence unique à la section pour éviter l'incohérence.
- Les comptes du plan général à 7 chiffres restent du côté GL; aucune nouvelle écriture de charge/produit sous prétexte de ventilation.
- Montants de ventes reconnus dans GL ≠ paiements encaissés en caisse; les transferts de caisse ne sont pas des produits.
- Ne pas affecter automatiquement tous les produits à l'agence de vente : distinguer lieu de vente, gare de départ et agence d'exploitation dans les attributs/rôles de l'axe AGC.
- Liens propriétaires et contrats historisés au jour économique pertinent; éviter le lien direct à `vehicule.proprietaire` actuel pour le passé.
- Pour achats stockés, l'achat est une entrée stock/fournisseur; charge véhicule lors de consommation comptablement appropriée, sans double comptage.
- Stocker IDs de société/site, sécurité multi-tenant, mode local/offline, dernière synchronisation; ne pas déclarer une donnée incomplète comme définitive.

## Migration progressive

1. Sauvegarde de base et tests de restauration. **Ne pas exécuter automatiquement sur une base existante**.
2. Créer les nouvelles tables (migration additive) sans supprimer ni changer `LigneEcriture.section` / `.vehicule`; migrer les alias « Gares » et « Agences » vers une hiérarchie logique en conservant les codes.
3. *Backfill* uniquement des lignes réellement validées où la source `section` ou `vehicule.section` est certaine. Si `section` et `vehicule.section` appartiennent à des plans différents : deux imputations dans deux plans, sans double montant dans le même plan. Si elles divergent au sein du même plan : **anomalie à arbitrer, ne pas dupliquer**.
4. Les dimensions propriétaires/contrats sont historisées avec date d'effet, pas reconstruites uniquement à partir du propriétaire actuel. Les axes sans preuve d'imputation restent « sans affectation ».
5. Tester total GL vs montants ventilés **plan par plan**, plan non affecté et écritures annulées; comparer les anciens états véhicule avec la nouvelle méthode, expliquer tout écart.
6. Synchroniser migrations et identifiants stables entre agences et siège; mettre en place idempotence et réconciliation après connexion.
7. Bascule contrôlée en production après validation comptable, plan de rollback et test d'une sauvegarde réelle.

## Pseudo-SQL de rapprochement, intention fonctionnelle seulement

```sql
-- Pour chaque plan: montant général admissible = affecté + non affecté
-- Ne pas additionner les montants de plans différents entre eux.
SELECT plan_code, SUM(charges_imputees), SUM(produits_imputes), SUM(non_affecte)
FROM vue_controle_plan_par_periode
WHERE date_gl BETWEEN :du AND :au AND ecriture_validee = 1
GROUP BY plan_code;
```
