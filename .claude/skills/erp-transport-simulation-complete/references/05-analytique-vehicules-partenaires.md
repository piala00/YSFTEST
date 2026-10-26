# Comptabilité analytique — uniquement deux familles visibles

## 1. États Véhicules
- Fiche, propriété datée, gamme VIP/Classique, agence d'exploitation, voyages/passagers (non monétaires), revenus billetterie, courrier transporté, carburant, pièces consommées, charges d'équipage, frais, quote-parts validées, redevances éventuelles et résultat après charges.
- `Grand livre analytique par véhicule` : toutes les lignes `analytic_allocation` avec `source_gl_line_id`, compte GA, pièce, dates, service, sous-tronçon.
- `Balance analytique par véhicule` : produits / charges par compte GL éligible, résultat, compte « NON_AFFECTE » distinct ; ne jamais rebaptiser le solde final financier « bilan SYSCOHADA du bus ».
- `Compte d'exploitation` : produits affectés moins charges affectées, variantes contributives (avant répartition) vs complètes (après charges communes).

## 2. États Propriétaires de véhicules
- Un propriétaire peut avoir plusieurs véhicules ; garder le **contrat et sa date d'effet**, prorata si changement durant la période.
- Restituer 3 **états séparés** : (a) compte d'exploitation des véhicules, (b) droits contractuels reconnus suivant contrat, (c) grand livre auxiliaire/situation financière du partenaire et solde bancaire payé/dû.
- Attention : le « résultat de véhicule » et le « solde payable au partenaire » sont deux mesures distinctes. Les paiements ne diminuent pas le résultat d'exploitation ; la dette partenaire doit provenir du GL.

## Intégrité des ventilations
- Chaque ventilation monétaire renvoie vers `gl_line_id` POSTED, avec affectation d'un montant signé, des dimensions : véhicule, propriétaire à la date des faits, service, agence vente, agence exploitation, gamme, ligne, voyage, contrat.
- Somme des ventilations (et NON_AFFECTE) pour une ligne GL = montant signé éligible de cette même ligne. Ne jamais sommer naïvement plusieurs dimensions indépendantes, sous peine de quadrupler les mêmes recettes.
- Une réimputation analytique ne change ni la somme ni la nature de la charge GL ; correction approbation + audit.
- Les coûts de paie d'équipage sont imputés sur la base des lignes 66 comptabilisées et du planning d'affectation réel ; la simulation simplifie « un équipage lié à un seul véhicule ».
- Les stocks ne deviennent charges qu'à consommation validée GA ; achats/commandes/entrées ne donnent pas d'écriture résultat analytique.

## Contrats de démonstration
15 bus privés, 10 partenaires. `70 % × MAX(0, recettes affectées au véhicule − charges contributives validées avant redevance)` est une **pure hypothèse pédagogique**, pas une norme de rémunération des propriétaires. La simulation comptabilise une redevance externe et paie 60 % du montant reconnu au 30/09, laissant 40 % dû. En production, signature du contrat, périmètre juridique des recettes et charges, TVA/taxes, rémunération brute ou nette et retenues déterminent la règle légale.
