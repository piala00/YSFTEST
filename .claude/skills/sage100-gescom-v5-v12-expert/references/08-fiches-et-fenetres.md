# 08 — Fenêtres, fiches, onglets et boutons : protocole de description

Le découpage V12 décrit des **rubriques fonctionnelles**, non un plan exhaustif des onglets dans chaque fiche. La liste qui suit sert à guider la lecture des écrans ; certains intitulés désignent des **rubriques à rechercher**, pas des onglets attestés. Afficher la mention [INDICATIF] tant qu'aucune capture V12 n'existe.

## 1. Liste de clients

**Chemin probable :** Structure > Clients.

À documenter : liste (numéro/nom/ville/solde et autres colonnes réellement affichées), barre de recherche, tri, filtres, raccourcis, création, édition, suppression, impression, éléments contextuels.

**Fiche client — rubriques métier recherchées :**
- Identification et contacts.
- Tarifs et représentant.
- Adresses et banques.
- Informations libres / bloc-notes / pièces jointes.
- Solvabilité (encours, code risque).
- Agenda.
- Paramètres : règlements, dépôt, devise, livraison, catégorie comptable.

**Ne pas dire** « les sept onglets exacts sont X, Y… » avant capture, car les libellés et la répartition visuelle diffèrent de la matrice.

## 2. Liste et fiche articles

**Chemin probable :** Structure > Articles.

**Rubriques métier recherchées :**
- Identification : référence, désignation, type, suivi du stock.
- Tarifs : clients, fournisseurs, catégories.
- Descriptif : catalogue, description, glossaire.
- Champs libres : informations/statistiques, documents et photo.
- Paramètres : ventes, escompte, options.
- Logistique : poids, codes-barres, délais, substitutions.
- Dépôts et emplacements : stock mini/maxi et paramètres locaux.
- Comptabilité et nomenclatures selon édition.

À vérifier spécialement : édition Standard/Premium, option Gamme, traçabilité Lot/Série, conditionnement, messages d'erreur et champs grisés.

## 3. Liste et fiche fournisseurs

**Chemin probable :** Structure > Fournisseurs.

Rubriques métier : identification, contacts, acheteur, tarifs/remises, banques, champs libres, solvabilité, agenda, conditions de paiement, dépôts, délais d'approvisionnement, options de facturation/transport.

## 4. Dépôts de stockage

**Chemin probable :** Structure > Dépôts de stockage.

Rechercher : liste des dépôts, détails d'identification, responsable/contact, paramètres stock, emplacements, utilisateurs, réapprovisionnement, souches documentaires. Selon licence, certains emplacements/fonctions sont indisponibles.

## 5. Document commercial de vente ou d'achat

**Chemin de regroupement :** Traitement > Documents des ventes/achats > type de document.

Relever trois zones séparées :

1. **En-tête** — numéro de pièce et souche, date, référence, client/fournisseur, devise, représentant/acheteur, dépôt et adresses (suivant document).
2. **Corps** — colonnes exactes, article, désignation, quantité, unité, prix, remises, taxes, stock, dépôt, lots et numéros de série (si présents).
3. **Pied** — bases HT/TVA/TTC, escompte, frais, acomptes, reste dû, statut, règlements (selon fonction).

**Boutons/actions à inspecter** : Ajouter ligne, Supprimer ligne, Transformer, Valider, Enregistrer, Imprimer, Aperçu, Annuler, Recherche, Traçabilité, Actions. Ne pas présumer que tous sont présents ni que leur libellé exact est identique.

## 6. Document de stock

Relever date, dépôt source, dépôt destination (transfert), motif, article, quantité, coût, traçabilité, validation et états d'impression. Un transfert ne doit pas être considéré comme vente, et une régularisation ne doit pas être considérée comme achat.

## 7. État ou rapport

Relever fenêtre de sélection, filtres, dates, périmètre, groupement, sortie PDF/impression, modèle, colonnes et totaux. Les capacités réelles d'export varient selon l'état et l'installation.

## 8. Fenêtre de personnalisation

Ouvrir `Fenêtre > Personnaliser`, noter les onglets réellement visibles et le contenu de chaque onglet. Exemples connus des anciennes versions : « Général », « Interface utilisateur » ; « Programmes externes » dans un contexte documentaire spécifique. Ne pas afficher ces noms comme universels sans capture locale.

## Structure recommandée d'une fiche UI

```text
Identifiant : UI-GESCOM-XXX
Version : V12.__ ; édition : ___ ; déploiement : ___
Utilisateur / droits : ___
Chemin d'accès : Menu > Groupe > Commande
Type : liste / fiche / document / état / assistant / dialogue
Origine de preuve : DOC-V12 / OBSERVÉ / ERG-CLASSIQUE / INDICATIF
Zone d'en-tête : ___
Onglets réellement visibles, ordre : ___
Sous-onglets : ___
Champs par onglet : ___
Colonnes de grille : ___
Boutons et icônes : ___
Actions : préconditions → effet → validation/confirmation
États : actif / inactif / masqué / lecture seule
Dépendances : licence, options, configuration, droits
Captures / références : ___
Points à clarifier : ___
```
