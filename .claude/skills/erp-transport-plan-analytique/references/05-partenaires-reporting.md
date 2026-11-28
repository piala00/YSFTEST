# 05 — Partenaires propriétaires et résultats de gestion

## Quatre couches distinctes

**1. Flotte / propriété juridique** : propriétaire d'un véhicule à la date donnée, avec documents.

**2. Contrat d'exploitation** : partenaire économique, pourcentage/forfait, dépenses éligibles, commissions, avances, dates d'effet, modalités de partage, règles de décompte. Le partenaire contractuel peut ne pas être le propriétaire juridique ; ne pas les fusionner par hypothèse.

**3. Compte d'exploitation analytique** : produits et charges du véhicule ventilés depuis billetterie, colis, carburant, garage, paie, assurance et frais communs justifiés.

**4. Compte auxiliaire financier** : dette ou créance du partenaire envers la société, décomptes validés, avances, règlements, compensations autorisées et solde restant.

La vue partenaire consolide tous ses véhicules mais n'est **pas** une consolidation comptable de sociétés au sens OHADA. Si l'exploitant n'est qu'intermédiaire plutôt que principal, les schémas légaux de reconnaissance de revenu seront différents : appliquer le modèle validé au contrat.

## État partenaire à produire

En-tête : compagnie, partenaire, contrat/version, période, statut des agences synchronisées, date et heure du calcul, devise, statut provisoire/définitif.

Détail par véhicule : classe Classique/VIP, voyages réalisés, km, sièges-km, billets, colis, remboursements, carburant, péages, garage, pièces, paie affectée, maintenance, autres coûts directs, frais communs, marges directes et complètes.

Situation financière : bases de commission/de partage et taux contractuel ; droits à régler, avances imputables, acomptes/payments, retenues justifiées, opérations en litige et solde initial/final. Driller jusqu'au billet, `shipment_leg`, ordre de réparation, bon carburant, décompte et facture, selon permissions.

## Illustration non réglementaire

Véhicule VIP de PART-03 sur la période : recettes retenues contractuellement 1 200 000 FCFA ; commission de gestion 15 % = 180 000 FCFA ; charges contractuelles imputables 400 000 FCFA ; droit théorique = 620 000 FCFA. Règlement antérieur applicable 100 000 FCFA ; à payer indicatif 520 000 FCFA, avant autre dette, taxes ou régularisation. **Ce chiffre peut différer de la marge économique du véhicule.**

## Tests spécifiques

- Même partenaire possède deux véhicules (Classique et VIP) : états séparés et total consolidé exact.
- Véhicule rattaché à PART-A jusqu'au 14 et à PART-B depuis le 15 : aucun transfert rétroactif des anciennes dépenses et recettes.
- Charge garage du véhicule dont le contrat rend le coût à la charge de la société : figure au compte économique du véhicule mais **n'est pas déduite** automatiquement de la dette au propriétaire.
- Versement partiel à un partenaire : diminue solde auxiliaire, ne diminue pas le résultat analytique.
- Contrat changé le jour du voyage : règle effective déterminée par moment de prestation ou clause approuvée, historisée avec version.
- Données partenaire accessibles seulement pour ses propres véhicules et contrats ; données personnelles voyageurs minimisées.
