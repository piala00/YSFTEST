# Écarts restants — comptabilité analytique (skill erp-transport-analytique-multiplans)

État au 26/10/2026, branche `ccr-5592a371-fusjt2`. « Fait » = codé et testé ; le reste est listé ici, sans prétendre
qu'il existe.

| # | Écart | Pourquoi ce n'est pas fait | Décision ou donnée attendue |
|---|---|---|---|
| 1 | **Ventilation fractionnée** (une ligne 100 000 → 60 000 car A + 40 000 car B dans un même plan ; refus de 100 % + 100 %) | Le moteur attribue une ligne à un seul élément par axe. Une table de ventilations dérivées (proposée par le skill) est un changement de structure : il faut d'abord savoir quelles charges répartir et selon quelles clés. | Liste des charges communes à répartir (assurance flotte, siège, loyers multi-gares…) et clés (km, voyages, places-km). Rien n'est réparti d'office en attendant. |
| 2 | **Canaux de vente** | Toutes les ventes passent par les guichets ; Mobile Money est un mode de paiement, pas un canal. Le produit est constaté au départ (une ligne par départ), il faudrait le fractionner par canal (écart 1). | Existe-t-il des revendeurs, une vente en ligne, des agents mobiles ? |
| 3 | **Agence administrative ≠ gare** | Une charge portant la section d'une agence (AG-) qui a plusieurs gares reste « non affectée » sur l'axe Gares. | Faut-il un axe « Agences (établissements) » distinct, regroupant leurs gares ? |
| 4 | **Droits par gare / par propriétaire** sur les états analytiques | Les droits existent par logiciel et par menu ; pas de filtre de données par gare ou par propriétaire. | Profils à restreindre (chef de gare, partenaire). |
| 5 | **Fraîcheur des données par agence** sur chaque état | Visible dans Fichier › Échanges ; pas encore en bandeau sur les états du siège. | — |
| 6 | **Exports PDF / Excel** | Impression navigateur (A4) et CSV ouvrable dans Excel disponibles ; pas de fichier PDF ou XLSX natif. | Format souhaité. |
| 7 | **Client bureau Windows** | La fenêtre « Comptabilité analytique » ouvre les états dans le navigateur (pas d'écran natif). | — |
| 8 | **Services : salaires répartis sur un véhicule** comptés « Conduite » | La ligne de paie ne garde pas l'employé ; un mécanicien imputé sur un véhicule serait compté en Conduite. | Accepter la règle, ou ajouter l'employé sur la ligne de paie. |
