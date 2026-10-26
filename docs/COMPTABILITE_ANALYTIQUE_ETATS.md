# Comptabilité analytique : plan analytique et états

Une seule comptabilité. Chaque montant analytique est une ligne de charge (classe 6) ou de produit (classe 7) d'une
écriture **validée** de la comptabilité générale. La comptabilité analytique ne saisit rien : elle attribue chaque
ligne aux éléments du plan analytique et regroupe. Le reporting et la consultation s'appuient sur les mêmes états.

## Où les trouver

Accueil › **Comptabilité analytique** › Etat › **Plan analytique (tous les axes)**, ou **États par axe**.
Aussi depuis Reporting › Etat › *Analyses par axe analytique*.

Parcours : **plan** (tous les axes) → **axe** (tous ses éléments) → **élément** (ses états détaillés).

## Le plan analytique

| Axe | Éléments | D'où vient l'attribution |
|---|---|---|
| Agences (gares) | chaque gare | section de gare de la ligne, sinon gare de départ du voyage, sinon l'agence (si une seule gare) |
| Véhicules | chaque car et camion | véhicule porté par la ligne d'écriture |
| Propriétaires | chaque propriétaire, et « Société (véhicules propres) » | contrat du véhicule **en vigueur à la date** de l'écriture |
| Services | billetterie, colis, conduite, garage, administration… | section du service posée par la paie (salaires hors véhicule) ; sinon le service qui produit le fait (billets → billetterie, colis → colis, carburant et route → conduite, garage → garage) |
| Gammes | Classique, VIP | gamme de la ligne du voyage, sinon flotte du véhicule à la date |
| Lignes (itinéraires) | chaque ligne | ligne du voyage |
| Voyages (départs) | chaque départ | pièce du départ, du colis, du plein, de la dépense, de l'avance de mission ou de l'imprévu |
| Activités | voyageurs, bagages, colis et fret, autres produits ; charges des véhicules, charges de structure | compte du produit ; charge rattachée ou non à un véhicule / voyage |
| Contrats des propriétaires | chaque contrat | contrat en vigueur à la date |
| Plans de sections | chaque section (services, projets…) | section portée par la ligne (Structure › Plan analytique) |

Une société de **commerce** n'a que ses plans de sections.

## Les états

Pour **chaque axe** : la balance de l'axe — produits, charges, résultat et marge de chaque élément, le **non affecté**
(qui reste en comptabilité générale, jamais réparti d'office) et le rapprochement : éléments + non affecté =
comptabilité générale.

Pour **chaque élément** (une gare, un véhicule, un propriétaire…), sept états :

1. **Compte d'exploitation** : produits et charges par rubrique (billetterie, bagages, colis ; carburant, route,
   garage, personnel, part du propriétaire…), résultat.
2. **Détail par compte** : chaque compte général, débit et crédit.
3. **Grand-livre analytique** : chaque ligne d'écriture avec date, pièce (cliquable), journal, compte et libellé.
4. **Évolution** : par jour (période de deux mois au plus) ou par mois.
5. **Ventilation croisée** : l'élément détaillé selon un autre axe (une gare par véhicule, un véhicule par ligne, un
   propriétaire par véhicule, les voyageurs par gamme…) ; chaque ligne mène à l'élément correspondant.
6. **Comparaison de périodes** : avec la période précédente de même durée ou la même période de l'année précédente
   (N-1), par compte, avec l'écart.
7. **Journal des imputations** : chaque ligne de l'élément avec son attribution sur tous les autres axes.

La balance d'un axe se **classe** par résultat, produits, charges ou nom. Le **non affecté** de chaque axe (anomalies
à examiner) s'ouvre depuis le plan.

Les états spécialisés restent disponibles : comptes d'exploitation, grand-livre et balance des véhicules ;
portefeuilles, relevés et règlements des propriétaires (situation financière **séparée** du résultat du véhicule) ;
balance analytique des sections.

## Consulter une période

Sur chaque écran : **Aujourd'hui, Hier, Cette semaine, Ce mois, Mois précédent, Ce trimestre, Cette année, Exercice**,
un **mois au choix** (mois + année), des dates libres, et les flèches **← période précédente / suivante →**. Une date de
début après la date de fin est refusée. Les écritures encore au brouillard sont signalées et ne sont pas comprises.
Chaque état s'imprime et s'exporte en CSV (Excel).

## Limites connues

- Une charge d'agence (section AG-) d'une agence qui a plusieurs gares reste « non affectée » sur l'axe Gares
  (elle n'est pas répartie d'office entre les gares).
- L'axe « canal de vente » n'existe pas : toutes les ventes passent par les guichets (Mobile Money est un mode de
  paiement). Une ligne n'est attribuée qu'à un élément par axe : pas encore de répartition 60/40 avec clés.
- Le reporting comparatif (Reporting › Transport : comparaisons) lit ses montants dans ce même moteur.
- Liste complète des écarts : `docs/retour/analytique/ECARTS_A_CORRIGER.md`.
