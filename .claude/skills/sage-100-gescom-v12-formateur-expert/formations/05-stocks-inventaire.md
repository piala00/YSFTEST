# Traitement — Stocks, transferts, inventaires et réapprovisionnement

Sources : matrice S1 ; Sage S7 FAQ fin d'année, S8 réapprovisionnement ; `references/05-menu-traitement.md`.

## Concepts indispensables

- Stock **physique** vs stock **disponible** vs stock **réservé** et autres quantités affichées selon installation.
- Dépôt / emplacement (si module disponible), article, mode de suivi de stock et valorisation.
- **Mouvement d'entrée** : entrée administrative/physique selon motif et paramétrage.
- **Mouvement de sortie** : sortie administrative/physique selon motif.
- **Mouvement de transfert** : changement de dépôt, *pas automatiquement vente*.
- **Inventaire** : comptage et régularisation d'écart à la date/contexte choisis.
- **Réapprovisionnement** : proposition selon mini/maxi par dépôt et besoins.

## Atelier 5.1 — Initialisation contrôlée

1. Créer l'article et dépôt fictifs (`Structure`), sans inventer un champ « stock initial » directement sur la fiche.
2. Relever stock initial/valorisation dans les états de contrôle.
3. Créer une entrée de 100 unités via `Traitement > Documents des stocks > Mouvement d'entrée` **ou** traiter une saisie d'inventaire selon procédure adaptée.
4. Contrôler après opération le mouvement, la quantité et la valeur ; relever l'identifiant de pièce.
5. Expliquer quel élément change la quantité et lequel se contente d'afficher la situation.

## Atelier 5.2 — Transfert entre dépôts

1. Dépôt A : 100 unités ; dépôt B : 0 unité (fictif).
2. Documenter mouvement de transfert de 25 unités A → B.
3. Relever avant/après : A, B et total tous dépôts.
4. Vérifier qu'un transfert **interne** ne doit pas être assimilé à une facture de vente. Tenir compte des exceptions de valorisation/paramétrage.
5. Tester le cas stock insuffisant en environnement de démonstration et noter avertissement/blocage effectif.

## Atelier 5.3 — Inventaire complet

Sage S7 distingue deux étapes : édition d'un **état préparatoire** via le menu `État`, puis **saisie d'inventaire** via le menu `Traitement`.

1. Figer le contexte de comptage (dépôt, date/période, équipe, règles d'exploitation).
2. Éditer l'état préparatoire en vérifiant les filtres.
3. Procéder au comptage physique fictif ; exemple théorique A = 73 alors que stock théorique = 75.
4. Renseigner le comptage via le mécanisme prévu, sans passer directement des SQL `UPDATE`.
5. Prévisualiser les écarts, les autorisations, la valorisation et la pièce de régularisation prévue.
6. Valider **uniquement** dans la base de test, puis vérifier mouvements et nouveaux stocks.
7. Éditer le livre/état après inventaire ; conserver le rapprochement comptage / système.

## Atelier 5.4 — Réapprovisionnement automatique

Sage S8 confirme que les seuils Mini/Maxi sont définis dans le **volet Paramètres – Dépôt des fiches articles**. La fonction peut proposer des commandes ou préparations de fabrication selon type d'approvisionnement.

1. Sur 2 dépôts, renseigner seuils distincts pour l'article de test.
2. Obtenir une situation en dessous du mini sur l'un des dépôts.
3. Ouvrir le traitement de réapprovisionnement autorisé ; contrôler le projet de proposition avant création de documents.
4. Vérifier la liste et expliquer pourquoi un dépôt figure ou non dans les besoins.
5. Consigner les documents générés, sans accepter aveuglément les quantités proposées.

## Grille de contrôle avant/après

| Opération | Mesure avant | Mesure après | Signal d'anomalie |
|---|---|---|---|
| Entrée | stock dépôt/lot | stock dépôt/lot | mauvaise référence/dépôt |
| Sortie | stock, réservation | stock, réservation | stock négatif inattendu |
| Transfert | A+B | A+B | total modifié sans cause |
| Inventaire | stock théorique/compté | écart/régularisé | double comptage, mauvaise date |
| Réapprovisionnement | mini/maxi, besoin | proposition créée | doublon de commande, seuil inadéquat |

## Notions expertes

Méthodes de valorisation (CMUP/FIFO/LIFO, selon options), traçabilité lots/séries, écart de coût, stocks négatifs, pièces en retard, multi-dépôts, comptage tournant, archivage. **Ne pas affirmer le calcul exact avant lecture des paramètres et de l'état**.
