# Imprévus du transport interurbain : analyse et traitement dans le logiciel

Principe : un imprévu ne doit ni faire disparaître une recette ni la compter deux fois. On garde le billet, on
trace l'imprévu sur le départ, et on passe seulement l'écriture de ce qui change réellement (argent rendu ou payé,
recette qui passe d'un car à un autre). Les comptes ci-dessous sont des **propositions à valider par
l'expert-comptable** ; ils sont modifiables sur chaque ligne.

## Catalogue

| # | Imprévu | Ce que fait le logiciel | Écriture |
|---|---|---|---|
| 1 | **Départ annulé par la compagnie** (panne avant le départ, route coupée, trop peu de voyageurs) | « Annuler le départ (compagnie) » : chaque voyageur est soit reporté sur un autre départ, soit remboursé **sans retenue** | Report : aucune ; remboursement : D 41911 / C caisse (ou remboursement autorisé 41913) |
| 2 | **Véhicule remplacé avant le départ** (panne, papiers) | Changer le véhicule du départ ; si la flotte diffère (VIP remplacé par un Classique), cocher « véhicule de remplacement » avec le motif : l'exception est tracée | Aucune ; la recette ira au car qui roule réellement |
| 3 | **Voyageurs VIP déclassés** (voyage fait en Classique) | Dédommagement : différence de tarif ou forfait, payé en caisse ou autorisé puis payé | D 709 rabais accordés (sur le véhicule) / C caisse |
| 4 | **Retard important** | Note sur le départ ; dédommagement éventuel (geste commercial) | Comme 3 |
| 5 | **Panne en route, transbordement** vers un autre car de la société | « Transbordement » : car de secours et part du trajet restant ; la recette (billets et bagages) est partagée | OD : D 70611/70614 car en panne / C 70611/70614 car de secours (même total) |
| 6 | **Car de secours loué** à un transporteur | Transbordement avec location : la recette reste au car en panne, qui porte le coût de la location | D 6228 location (car en panne) / C caisse ou 401 loueur |
| 7 | **Dépannage, remorquage** | Frais d'imprévu | D 624 (car en panne) / C caisse ou 401 |
| 8 | **Voyageurs bloqués** (repas, hébergement) | Frais d'imprévu | D 638 / C caisse |
| 9 | **Accident** : réparation du car | Ordre de réparation au garage (déjà existant) | D 624 / C caisse ou 401 |
| 10 | **Accident** : indemnisation de voyageurs ou de tiers | Frais d'imprévu | D 658 / C caisse ou 401 |
| 11 | **Bagage ou colis perdu ou abîmé** | Frais d'imprévu « indemnité » | D 658 / C caisse |
| 12 | **Amende, contravention** | Frais d'imprévu ; si la faute est celle du chauffeur, « imputable au chauffeur » : retenue sur salaire | Charge : D 658 / C caisse ; chauffeur : D 421 / C caisse |
| 13 | **Voyageur pris en route sans billet** (vente à bord) | « Recette à bord » remise à l'arrivée par le convoyeur | D caisse / C 70611 (sur le car) |
| 14 | **Voyageur absent au départ** | Déjà traité : liste d'embarquement, billet à reporter ou rembourser | Aucune au départ |
| 15 | **Carburant ou péage imprévus en route** | Justificatifs de l'avance de mission (déjà traité) | D 6053 / 638 / C 47121 |
| 16 | **Remboursement de l'assurance** | Écriture à la réception (comptabilité) | D banque / C produit à définir avec l'expert-comptable |
| 17 | **Changement de chauffeur en route** | Note sur l'imprévu (pas d'argent) | Aucune |

## Règles

- La recette d'un billet est constatée une fois, au départ du car. Un transbordement **déplace** une part de cette
  recette d'un car à l'autre ; il n'en crée pas.
- Un dédommagement réduit la recette (709, rabais accordés) ; ce n'est pas une nouvelle charge d'exploitation.
- Les frais d'imprévu sont imputés au véhicule concerné, donc visibles dans son compte d'exploitation.
- Chaque imprévu garde : départ, date, lieu, description, auteur, pièces et écritures (drill-down).
