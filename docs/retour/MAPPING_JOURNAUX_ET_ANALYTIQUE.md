# Journaux, comptes et analytique (tous les comptes sont des PROPOSITIONS à valider)

**Plan à 7 chiffres.** Un nouveau dossier (Commerce comme Transport) a un plan comptable à 7 chiffres : les numéros
ci-dessous sont écrits courts et complétés par des zéros à droite (4111 → 4111000, 41911 → 4191100, 467 → 4670000).
Les regroupements par préfixe (classe, compte à 2 ou 3 chiffres) restent identiques. Un dossier existant passe à
7 chiffres par `python manage.py longueur_comptes --appliquer` (refusé si deux comptes se confondraient). Un dossier
repris d'un autre logiciel garde son plan d'origine tel quel jusqu'à la bascule.

## Journaux
| Code | Usage |
|---|---|
| CA (et CA-xxx au siège) | Caisse espèces de l'agence (5711) |
| MM | Mobile Money (552 pour les nouveaux dossiers ; 551 = carte carburant) |
| BQ | Banque (5211) |
| VT / AC | Ventes et achats en compte |
| OD | Recettes constatées au départ, décomptes propriétaires, régularisations, transbordements |

## Schémas principaux
| Fait | Écriture | Véhicule sur la ligne |
|---|---|---|
| Vente d'un billet (et bagages) | D caisse / C 41911 | non (avance du voyageur) |
| Départ du car | D 41911 (ou liaison 185) / C 70611 billets, 70614 bagages | oui (part de chaque tronçon) |
| Colis port payé | D caisse / C 41912 puis au départ D 41912 / C 70612 ou 70613 | oui au départ |
| Annulation (retenue) | D 41911 / C caisse ou 41913 / C 70611 retenue | non |
| Dépense véhicule, carburant, réparation | D 6053, 624… / C caisse ou 401 | oui |
| Avance de mission | D 47121 / C caisse ; justification D 638, 6181, 6053, 624 / C 47121 | oui |
| Paie | D 661, 664… / C 422, 431… (taux fixés par l'expert-comptable) | selon la ventilation de l'employé |
| Droit du propriétaire | D 622 (fixe, variable) / C 467 propriétaire | oui (622) |
| Contrat type du propriétaire (compte du camion) | fixe mensuel éventuel : D 622 / C 467 ; compte du camion = recettes − dépenses à sa charge (carburant, route, réparations) − pourcentage de la société sur les recettes : D 622 / C 467 (ou l'inverse s'il est négatif) ; assurances et papiers : charges de la société, jamais déduites | oui (622) |
| Avance, retrait, règlement au propriétaire | D 467 / C caisse | non |
| Dépense de fonctionnement d'une autre agence | payeur D 185 agence / C caisse ; agence concernée D charge / C 185 payeur | si indiqué |
| Achat du magasin pour le stock | D 33x stock / C 401 fournisseur (journal AC) ou caisse | non |
| Achat pour un véhicule précis | D charge (624, 6047…) / C 401 ou caisse | oui |
| Achat d'un matériel durable | D classe 2 (244 par défaut) / C 401 ou caisse | non |
| Sortie du magasin (réparation, emballage, bureau) | D charge au coût moyen / C 33x | oui si un véhicule est indiqué |
| Transfert de fonds | D 585 / C caisse puis D banque / C 585 | non |
| Imprévus | 709 dédommagement, 6228 location de secours, 624 dépannage, 638 voyageurs bloqués, 658 indemnités et amendes, 421 amende imputable au chauffeur | oui |
| Écart de caisse | D 658 ou 421 / C caisse ; D caisse / C 758 | non |

## Analytique
- Une seule écriture générale par fait ; le véhicule est une colonne de la ligne (`LigneEcriture.vehicule`), la gare ou l'agence une section analytique.
- Comptabilité analytique : deux rubriques, **Véhicules** (compte d'exploitation, rapprochement affecté / non affecté) et **Propriétaires** (portefeuille selon le contrat en vigueur à la date de chaque écriture ; situation financière séparée).
- Reporting : comparaisons par agence, Classique / VIP, ligne, véhicule, propriétaire sur les mêmes écritures.
