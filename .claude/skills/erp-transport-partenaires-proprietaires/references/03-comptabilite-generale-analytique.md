# 03 — Comptabilité générale source unique des opérations propriétaires

## Chaîne de traitement obligatoire
Prestation/voyage → sous-journal opérationnel → écritures comptables générales selon contrat et règles approuvées → validation (GA) → écritures d'imputation analytique en **référence au GL existant** → états Véhicules/Propriétaires → reporting. Les montants monétaires non validés sont « prévisions » ou « provisoires », jamais « soldes comptables définitifs ».

## Déclenchements types (aucun compte imposé avant vérification OHADA)
1. Réalisation de transport : produit et créance/encaissement selon le rôle de la compagnie, les règles fiscales et la période comptable.
2. Carburant, garage, salaire salarié, fournitures **consommées** : comptes de charges ou immobilisations/stocks appropriés, jamais doubler achat + consommation.
3. Droit de rémunération fixe : reconnaissance du montant dû selon l'obligation juridique, son exigibilité et la nature (charge ou compte d'avance, etc.), dans un sous-compte tiers propriétaire distinct.
4. Rémunération variable : acte/décompte validé ; comptabilisation du droit **sans le dupliquer** si déjà constaté lors des prestations.
5. Versement fixe / retrait complémentaire : débit du compte de dette propriétaire, crédit de trésorerie (ou traitement d'avance si paiement précédant la constatation du droit). **Un paiement n'est pas une nouvelle charge si celle-ci a déjà été reconnue.**
6. Correction : annulation/contrepassation et nouveau mouvement lié, jamais destruction du détail historique.

## Contrôle des imputations
`analytic_distribution` : `distribution_id`, `source_gl_line_id` (FK vers ligne GA `POSTED`), `allocation_amount_signed`, `vehicle_id`, `owner_id`, `agency_id`, `journey_id`, `contract_id`, `period`, `rule_version`. Les allocations ne doivent pas excéder les montants éligibles de leur ligne source. Les écritures de trésorerie, de dette partenaire et les écritures de bilan **n'entrent pas dans les charges/produits analytiques par accident**. Un relevé financier propriétaire les exploite cependant à partir de la GA.

Les états du propriétaire ne doivent pas présenter les recettes totales de ses véhicules comme des sommes dues : les recettes relèvent du **compte d'exploitation véhicule**, tandis que les droits propriétaires sont calculés et comptabilisés séparément.

## Cas de comptabilisation variable
En comptabilité générale, si la compagnie agit comme intermédiaire pour le compte d'un propriétaire, il peut falloir un traitement différent de la vente en propre. Seule l'analyse du contrat permet de déterminer comment présenter produits, charges et fonds pour compte de tiers. Soumettre les modèles d'écritures à un professionnel SYSCOHADA/impôts au Cameroun avant mise en production.
