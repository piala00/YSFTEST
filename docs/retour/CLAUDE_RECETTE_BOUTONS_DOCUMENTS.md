# Recette des boutons affichés sur les pièces commerciales

Produit par `python manage.py recette_boutons_documents` (base de recette, administrateur).
Chaque fiche est réellement affichée ; on compte dans la zone de travail les liens et boutons actifs,
et les commandes grisées (inactives ou désactivées). Les numéros de pièces liées ne sont pas des commandes.

- Combinaisons type × statut : **84** ; fiches affichées : **77** ; sans objet : **7** (types qui ne se transforment pas).
- Erreurs d'affichage (code HTTP différent de 200) : **0**.

| Type | Brouillon | Validé | Transformé | Annulé |
|---|---|---|---|---|
| Devis | 14 / 4 | 17 / 3 | 12 / 4 | 11 / 4 |
| Bon de commande | 14 / 4 | 17 / 3 | 12 / 4 | 11 / 4 |
| Préparation de livraison | 14 / 4 | 15 / 3 | 12 / 4 | 11 / 4 |
| Bon de livraison | 14 / 4 | 15 / 3 | 12 / 4 | 11 / 4 |
| Bon de retour | 14 / 4 | 14 / 3 | 12 / 4 | 11 / 4 |
| Bon d'avoir financier | 14 / 4 | 14 / 3 | 12 / 4 | 11 / 4 |
| Facture | 14 / 4 | 17 / 2 | 14 / 3 | 11 / 4 |
| Facture de retour | 14 / 4 | 13 / 3 | — | 11 / 4 |
| Facture d'avoir | 14 / 4 | 13 / 3 | — | 11 / 4 |
| Demande d'achat | 14 / 4 | 15 / 3 | 12 / 4 | 11 / 4 |
| Préparation de commande | 14 / 4 | 15 / 3 | 12 / 4 | 11 / 4 |
| Bon de commande fournisseur | 14 / 4 | 16 / 3 | 12 / 4 | 11 / 4 |
| Bon de livraison fournisseur | 14 / 4 | 15 / 3 | 12 / 4 | 11 / 4 |
| Bon de retour fournisseur | 14 / 4 | 14 / 3 | 12 / 4 | 11 / 4 |
| Bon d'avoir financier fournisseur | 14 / 4 | 14 / 3 | 12 / 4 | 11 / 4 |
| Facture fournisseur | 14 / 4 | 17 / 2 | 14 / 3 | 11 / 4 |
| Facture de retour fournisseur | 14 / 4 | 13 / 3 | — | 11 / 4 |
| Facture d'avoir fournisseur | 14 / 4 | 13 / 3 | — | 11 / 4 |
| Mouvement d'entrée | 12 / 4 | 10 / 4 | — | 9 / 4 |
| Mouvement de sortie | 12 / 4 | 10 / 4 | — | 9 / 4 |
| Mouvement de transfert | 12 / 4 | 10 / 4 | — | 9 / 4 |

Cases : commandes actives / grisées. « — » : sans objet.

## Commandes actives selon le statut

- **BROUILLON** : Annuler, Annuler la pièce, Client de recette, Fiche du tiers, Fonctions, Fournisseur de recette, Imprimer, Informations, Modifier la pièce, Nouveau, OK, Valider la pièce
- **VALIDE** : Annuler, Annuler la pièce, Bon de commande, Bon de commande fournisseur, Bon de livraison, Bon de livraison fournisseur, Bon de retour, Bon de retour fournisseur, Client de recette, Comptabiliser, Facture, Facture d'avoir, Facture d'avoir fournisseur, Facture de retour, Facture de retour fournisseur, Facture fournisseur, Fiche du tiers, Fonctions, Fournisseur de recette, Imprimer, Informations, Nouveau, OK, Préparation de commande, Préparation de livraison, Saisir un acompte (paiement d'avance), Saisir un règlement, Transformer
- **TRANSFORME** : Annuler, Client de recette, Comptabiliser, Fiche du tiers, Fonctions, Fournisseur de recette, Imprimer, Informations, Nouveau, OK
- **ANNULE** : Annuler, Client de recette, Fiche du tiers, Fonctions, Fournisseur de recette, Imprimer, Informations, Nouveau, OK

## Vérification des « écarts critiques » signalés par GPT (27/10/2026)

| Constat GPT | Vérifié dans le code | Avis de Claude |
|---|---|---|
| « Comptabiliser » n'ouvre que l'écriture existante | Oui : les factures et avoirs sont comptabilisés **à la validation** (`Document.valider`). Le bouton mène à l'écriture produite ; il est grisé sur les pièces non comptables. | Choix de conception voulu, sans risque comptable : une pièce validée a toujours son écriture. Pour une mise à jour comptable différée (par lots), il faudrait une décision du propriétaire, pas un bouton de plus. |
| La liste « Actions » ne propose qu'Imprimer et Actualiser | Oui. | Écart réel avec le logiciel de référence : à compléter, par exemple avec la transformation et la validation en série, en gardant les mêmes contrôles côté serveur. |
| « Supprimer » de la liste appelle une **annulation** | Oui : il n'est actif que sur une pièce **en brouillon** (`data-modifiable="1"`), et la pièce passe au statut Annulé (rien n'est effacé, traçabilité gardée). | Comportement sûr. Seul le libellé trompe : proposer « Annuler la pièce » comme sur la fiche. |
| Sept commandes inactives dans la saisie de pièce | Oui : 2 à 4 commandes grisées par fiche selon le statut (tableau ci-dessus). | Ce sont des fonctions non développées, affichées grisées comme dans le logiciel de référence. À réaliser une par une, ou à masquer si elles ne sont pas prévues. |

Autres observations de la recette :
- « Annuler la pièce » est absent des factures validées (fournisseurs compris) : c'est correct, une facture validée se corrige par un avoir.
- « Saisir un règlement » n'apparaît que sur les factures validées. Pour un **avoir** client ou fournisseur validé, aucun bouton ne permet de saisir le remboursement depuis la pièce. À examiner avec GPT, sans rien inventer de la référence.
- Angles morts que ni le recensement statique ni cette recette ne couvrent encore : les **droits par profil** (la recette se fait en administrateur) et les **listes** (une liste par type × filtres). Prochaine étape proposée : la même recette avec un profil restreint.
