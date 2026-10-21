# Traitement — Cycle des achats et réception fournisseurs

Menu : `Traitement > Documents des achats` [DOC-V12], avec demande d'achat, préparation de commande, bon de commande, bon de livraison, retours, factures et avoirs selon édition.

## Processus d'apprentissage

`Besoin article → demande/préparation → bon de commande → réception contrôlée → BL fournisseur → facture d'achat → bon à payer (si activé) → règlement → retour éventuel`

Ne pas confondre la **commande fournisseur**, qui exprime un engagement, et la **réception physique**, qui constate l'arrivée de marchandises. Contrôler le mouvement de stock effectif sur l'état des mouvements.

## Atelier 4.1 — Achat classique

1. Vérifier article, fournisseur, référence fournisseur, unité d'achat, dépôt de destination, taxes.
2. Créer une commande fournisseur de 30 unités fictives `JUS-001` ; relever quantité, prix, dates, souche, fournisseur.
3. Effectuer une réception **partielle** de 20 unités sur dossier test lorsque le processus permet la réception partielle ; noter le reliquat.
4. Rapprocher réception, document de livraison et facture selon écrans disponibles.
5. Contrôler les quantités reçues, les coûts, les écarts de prix et l'incidence stock.
6. Enregistrer la facture fournisseur ; vérifier si bon à payer et transfert comptable sont configurés.
7. Rechercher chaque pièce et prouver leur lien ; expliquer ce qui reste à recevoir.

## Atelier 4.2 — Bon à payer (édition/paramètre dépendant)

La fiche Sage S9 décrit un circuit pouvant attribuer la conformité de facture à l'acheteur et l'autorisation de paiement au responsable financier. Vérifier les paramètres dans `Fichier > Paramètres société > Documents > Gestion du bon à payer` **sur le dossier concerné**.

Questions : niveau de validation ? qui peut autoriser ? que signifie « facture contrôlée » vs « payée » ? quelle traçabilité ?

## Atelier 4.3 — Retour fournisseur

Préparer un scénario où 2 unités réceptionnées sont refusées. Identifier la pièce réellement prévue, vérifier **sortie de stock physique** et **conséquence sur dette fournisseur**, en faisant le rapprochement des pièces ; ne pas utiliser un avoir seul comme preuve de retour physique.

## Audit des erreurs

- Réception absente : filtrage, dépôt, statut, commande, droits.
- Facture non rapprochée : références pièces, quantités partielles, fournisseur, prix, flux de transformation.
- Dette fournisseur incohérente : échéance vs règlement, avoir, mise à jour comptable.
- Coût de stock inattendu : méthode de valorisation, date de réception, frais et revalorisations ; analyser avant correction.

**Sources** : matrice fonctionnelle S1 ; procédure bon à payer S9 ; réapprovisionnement S8.
