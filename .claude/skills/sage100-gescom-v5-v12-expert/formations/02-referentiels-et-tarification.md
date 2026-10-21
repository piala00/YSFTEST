# Menu Structure — Articles, tiers, dépôts, familles et tarifs

Source : `references/04-menu-structure.md` [DOC-V12]. Les sous-rubriques décrites sont **fonctionnelles**, pas forcément les intitulés exacts d'onglets dans chaque V12.

## Les références à connaître et leurs liaisons

| Référence | Prérequis | Rôle métier | Liée à |
|---|---|---|---|
| Famille d'articles | politique de suivi/tarif | valeurs communes aux articles | articles, statistiques, comptabilité |
| Article | famille, unités, référence, suivi | élément vendu, acheté ou géré en stock | tarifs, documents, dépôts, lots selon option |
| Client | compte, catégorie tarifaire, règlement | tiers acheteur | vente, encours, factures, échéances |
| Fournisseur | compte, règlement et livraison | tiers approvisionneur | achats, tarifs fournisseurs, délais |
| Dépôt | règles de logistique | lieu/organisation de stock | stock par dépôt, mouvements, inventaires |
| Collaborateur | rôle commercial | responsable de certaines opérations | représentant, commissions, états |
| Barèmes | catégories / taux | remises, RRR, promotions, commissions | tarifs et ventes |
| Plan comptable et taxes | paramètres société | affectation des comptes et taxes | achats, ventes, transfert comptable |

## Atelier 2.1 — Créer et expliquer une fiche article

1. Dans dossier test, choisir `Structure > Familles d'articles`, créer/relever la famille BOISSONS (libellé fictif).
2. Choisir `Structure > Articles`, créer un article exemple `JUS-001` « Jus mangue 1 L ».
3. Relever sur écran réel : champs obligatoires, unité de vente, type de suivi de stock, catégorie de tarif, prix d'achat, prix de vente et traitement TVA selon dossier.
4. Vérifier l'effet de la famille sur l'article : recopies, valeurs proposées, cas non hérités.
5. Ouvrir les informations de dépôt disponibles pour voir mini/maxi et conditions de réapprovisionnement.
6. Dans la liste articles, rechercher `JUS-001`; classer les colonnes et boutons réellement affichés [OBSERVÉ].
7. **Ne pas saisir une quantité de stock initial directement dans la fiche en supposant que cela génère une entrée** : utiliser la procédure d'entrée stock/inventaire prévue par Sage. Voir `formations/05-stocks-inventaire.md`.

## Atelier 2.2 — Client, fournisseur, tarifs et solvabilité

1. Créer client fictif `CLI-001`, fournisseur `FOU-001` et affecter leurs modes de règlement.
2. Comparer les rubriques Tarifs, Identification, Adresses, contacts et solvabilité **observées**.
3. Fixer un plafond d'encours sur un client de test si l'édition le permet ; expliquer **avertissement** vs **blocage**, sans supposer la règle exacte tant que le paramétrage de livraison n'a pas été examiné.
4. Configurer deux catégories tarifaires fictives (GROS et DÉTAIL), relever comment les prix varient pour le même article.
5. Créer une remise de quantité *si* le dossier et l'édition permettent cette fonction ; vérifier le calcul sur un document test.

## Les pièges à connaître

- Le **tarif client** peut provenir de catégorie tarifaire, remise, tarif exceptionnel ou autre règle. Ne jamais expliquer un prix calculé sans tracer sa source.
- La fonction **« Recalculer le prix de vente » lors d'une transformation** peut tenir compte du prix de revient et d'un coefficient dans des conditions spécifiques : ne pas dire qu'elle recalcule systématiquement tous les prix. Source Sage S11.
- Les **documents attachés** sont documentés par Sage dans `Structure > Articles / Clients / Fournisseur > Champs libres > Documents attachés`, mais peuvent dépendre du déploiement ; S10.
- Ne pas changer sans étude le mode de suivi stock d'un article déjà utilisé.

## Compétence à démontrer

Définir deux clients avec des conditions différentes et produire, pour le même article, une comparaison des prix documentée : paramètres → fiche client → fiche article → devis test → résultat. Expliquer les écarts.
