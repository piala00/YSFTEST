# Traitements et options avancés — Ce qu'un expert doit savoir identifier

Sources : S1, S6, S8, S9, S11 ; `references/05-menu-traitement.md` et `references/09-disponibilite-et-droits.md`.

| Fonction | Utilité et interactions à maîtriser | Risque de mauvaise interprétation |
|---|---|---|
| Fabrication | Nomenclature, préparation, ordre, avancement, bon de fabrication | Confondre composants et produits finis ou impacts stock |
| Contremarque | Achat/fabrication liée à un besoin client | Croire qu'un achat lié est une vente ou vice versa |
| Gestion des affaires | Affaire, coûts, marge, facturation à l'affaire | Fusionner chiffre d'affaires affaire et facture sans contrôle |
| Prestations/services | Prestations types, abonnements, échéances | Assimiler service à produit stocké |
| Bon à payer | Contrôle acheteur et décision responsable financier | Confondre « contrôlé » et « payé » |
| Planning ressources | Disponibilité, réservations et allocation | Prendre une réservation pour une livraison |
| Traçabilité lot/série | Suivi des identifiants par mouvement | Tracer seulement l'article sans le lot/numéro |
| Logistique | Préparation, réceptions, contrôles et livraison | Ignorer emplacements et statuts intermédiaires |
| Statistiques représentants | Attribution, commission, périodes et exclusions | Sous-estimer les avoirs / changements d'affectation |

## Méthode de formation pour chaque option

1. Confirmer édition/module et droit.
2. Ouvrir paramètres puis enregistrement source avant le traitement.
3. Réaliser sur un dossier test un scénario **normal** et un scénario **d'exception** (manquant, retard, partiel, refus).
4. Tracer documents et incidences avant/après.
5. Construire une fiche champ par champ avec capture.
6. Demander à l'utilisateur d'expliquer pourquoi le résultat change avec l'option désactivée.

## Exemple pédagogique : bon à payer

- Lire S9 et localiser `Fichier > Paramètres société > Documents > Gestion du bon à payer` si cette fonction est présente.
- Distinguer les niveaux **aucun**, **responsable financier**, **acheteur + responsable financier** tels qu'expliqués dans S9 (paramétrage à vérifier en V12.xx).
- Sur facture d'achat fictive, relever qui peut déclencher chaque étape et quel statut résulte.
- Examiner la journalisation des validations ; ne pas contourner les droits.

## Exemple pédagogique : tarif recalculé à la transformation

- Source S11 : l'option « Recalculer le prix de vente » a une logique conditionnelle liée notamment au prix de revient et coefficient selon la tarification de l'article.
- Préparer vente avec article, catégorie et coefficients fictifs ; comparer scénario option active/inactive sans modifier les données de production.
- Expliquer pourquoi une transformation peut donner un tarif différent sans qu'il y ait nécessairement erreur de stock.
