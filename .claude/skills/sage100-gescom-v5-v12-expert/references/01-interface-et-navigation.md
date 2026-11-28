# 01 — Fenêtre principale, navigation et barres [ERG-CLASSIQUE]

## Plan de l'interface Windows

1. **Barre de titre** : nom de l'application, société/dossier, commandes système minimiser/agrandir/fermer.
2. **Barre de menus** : Fichier · Édition · Structure · Traitement · État · Fenêtre · ? ; les cinq menus métier Fichier, Structure, Traitement, État, Fenêtre sont confirmés dans S1.
3. **Barres d'outils configurables** : commandes rapides de navigation, création, recherche, impression ; contenu exact à relever selon poste utilisateur.
4. **Barre verticale de navigation** : raccourcis regroupés par thèmes, affichage et composition personnalisables depuis Fenêtre.
5. **Espace de travail** : fenêtre(s) actives, listes, formulaires, zones de recherche et de filtre.
6. **Barre d'état** : informations de contexte/dossier et états de traitement, selon la configuration.
7. **Accueil éventuel IntuiSage / favoris** : ergonomie connue dans les versions précédentes, mais **ne pas promettre ses onglets sur toute V12**.

## Commandes usuelles de navigation (libellés indicatifs à confirmer dans la V12 locale)

| Action | Usage attendu | À vérifier |
|---|---|---|
| Ajouter | Nouvelle fiche ou nouvelle ligne | Icône, raccourci, droits, fenêtre active |
| Consulter | Ouvrir sans modifier | Mode réel et permissions |
| Voir/Modifier | Modifier une fiche | Libellé actuel et états autorisés |
| Supprimer | Supprimer l'élément sélectionné | Confirmation, interdictions métier |
| Précédent / Suivant | Parcourir les enregistrements | Sens, portée, tri actif |
| Rechercher / Atteindre | Retrouver un enregistrement | Critères, raccourcis |
| Trier / Filtrer | Ordonner ou limiter les lignes | Menus contextuels / entêtes de colonnes |
| Actualiser | Rafraîchir une liste | Commande `Fenêtre > Actualiser` [DOC-V12] |
| Imprimer / Aperçu | Éditer un état, modèle d'impression | Modèles et imprimantes |
| Dupliquer | Créer par copie si fonction autorisée | Contexte métier |

## Liste vs fiche vs boîte de dialogue

**Liste :** tableau d'enregistrements. Relever les colonnes, format, icônes, zone de recherche, filtrage, tri, pagination éventuelle, menu contextuel, boutons et sélections multiples.

**Fiche :** écran d'un tiers/article/dépôt/ressource. Relever bandeau d'identification, zones obligatoires, onglets réels, champs, boutons et validation/annulation, éléments masqués selon profil.

**Document :** écran de devis/commande/BL/facture/mouvement. Relever type, numéro, dates, tiers/dépôt, lignes de document, prix/taxes, totaux, validation, transformation, impression et traçabilité.

**Assistant :** procédure guidée ; relever les étapes et messages, ne pas transformer cela en « onglet » sans vérification.

## Personnalisation

`Fenêtre > Personnaliser`, `Fenêtre > Personnaliser les écrans`, `Fenêtre > Personnaliser la liste`, `Fenêtre > Barre verticale`, `Fenêtre > Préférences` sont des entrées [DOC-V12].

La position des barres, la taille des icônes, les colonnes et les éléments visibles sont potentiellement propres au poste ou au profil. Une capture ancienne ne remplace pas une capture V12.
