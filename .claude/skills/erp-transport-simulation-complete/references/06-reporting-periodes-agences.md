# Reporting et tableaux comparatifs de direction

## Modules et filtres
Un **module Reporting indépendant** de l'interface Comptabilité analytique. Il lit les produits/charges de la GA via le moteur analytique, et complète les indicateurs non monétaires des voyages, embarquements, colis, RH et stocks.

Comparer jour/semaine/mois/trimestre/année/période personnalisée ; par agence de vente **et** agence d'exploitation (deux dimensions distinctes), par véhicule, gamme VIP/Classique, ligne, propriétaire, activité, service, caisse, source paiement.

## États attendus
- Tableaux simples journaliers agence : date, véhicules, trajet, places réellement embarquées, tarif unitaire/part trajet, total billetterie, bagages, courrier, dépenses sorties de caisse, recette nette, montant reversé et solde par caisse.
- Tableau « performance véhicules » : trajets, kilométrage, personnes, recettes voyage/colis, coûts carburant/garage/paie, résultat analytique sourcé, marge, total période, comparatifs J/J-1 et M/M-1.
- « Performance agences » : billetterie **exploitée** vs billets **encaissés**, courrier, dépenses affectées, flux caisse, opérations en attente de synchro ; identifier transfert siège, ne pas classer un virement comme une recette.
- « Partenaires » : performance de chacun de leurs véhicules, droits, avances/règlements issus GA, balance partenaire ; drill-down jusqu'aux pièces.
- « Achats » : volume BC/factures, stocks et ruptures, distribution par dépôt, consommations garage/courrier/bureau, engagement fournisseur et comptes 401.
- « RH » : masse salariale GA, rémunérations par service/agence/équipage, paies versées/dues, comparatifs par période.
- « Trésorerie » : ouverture, encaissements par mode, sorties, transferts, banque, caisse de service, rapprochements, anomalies de solde négatif.

## Pas de faux comparatifs
Fournir SEPTEMBRE 2026 complet. Le mois précédent / suivant non alimenté = **non disponible**, jamais `0` ou une courbe fabriquée. Les comparaisons entre les huit agences du même mois sont possibles et testables, ainsi que les comparaisons semaines/semaine pendant septembre.

## Source GL prioritaire
Chaque cellule financière permet drill-down vers ventilation analytique → ligne GL comptabilisée → pièce source. Les données d'exploitation n'injectent jamais de charge fictive en analytique. Tout montant hors GA se trouve seulement dans une section **prévision/projeté/non comptabilisé** clairement séparée.
