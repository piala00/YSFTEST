# Audit fonctionnel — lot 05 : saisie des documents commerciaux

**Périmètre :** formulaire commun aux 21 types de documents de vente (9), achat (9), stock (3). Branche distincte de la PR #4 pour ne pas annuler ses tests.

## Comportement ERP constaté avant modification
La barre de la fenêtre de saisie affichait les commandes **Fonctions, Barèmes, Informations, Pied, Imprimer, Comptabiliser, Transformer** sous forme de \`span.inactif\`. En revanche, le formulaire disposait déjà des véritables actions **OK = enregistrer le brouillon**, **Valider la pièce** (confirmation avant POST) et **Nouveau** pour ajouter une ligne.

## Lot 05 — trois commandes rendues opérationnelles

| Commande | Action réalisée | Sécurité |
|---|---|---|
| Fonctions | Menu déroulant : Enregistrer le brouillon, Valider la pièce…, Ajouter une ligne | Appelle les **boutons du formulaire existants**, y compris la confirmation d'origine ; aucune nouvelle route ou écriture |
| Informations | Affiche/masque un panneau indiquant type, numéro ou état non enregistré, statut et origine éventuelle | Informations en lecture seule ; aucune mutation |
| Pied | Place la zone des totaux dans le champ de vision et lui donne le focus | Aucun calcul supplémentaire, aucune modification du montant |

**Toujours inactives à dessein :** Barèmes, Imprimer, Comptabiliser, Transformer dans le formulaire de saisie. L'impression d'un brouillon non sauvegardé ou sa transformation immédiate sont potentiellement trompeuses ; la consultation/impression et les transformations demeurent dans la fiche du document enregistré. « Comptabiliser » ne doit pas créer de doublon : la comptabilisation est actuellement déclenchée à la validation pour les pièces de facturation.

**Vérification Sage 100 V12 :** les intitulés des commandes ne prouvent pas leur déroulement exact ; cette implémentation est une **amélioration fonctionnelle ERP**, pas une certification d'identité avec Sage V12. Des captures sur installation de référence et un inventaire de l'édition sont nécessaires pour préciser les comportements originaux.

## Tests et revue Claude Code
- Les tests JavaScript déjà exécutés restent dans \`tests_js/test_menus_actions.js\`, avec 8 contrôles supplémentaires de la nouvelle barre.
- Le workflow existant \`audit-boutons.yml\` exécute ce fichier : aucun workflow supplémentaire et aucun commit automatique ajouté.
- La suite Django et les compilations Windows/SQL Server doivent réussir dans la CI de la PR avant fusion.
- La recette navigateur doit vérifier le clic sur les trois commandes, l'absence de soumission involontaire, le menu déroulant Bootstrap, la confirmation Valider d'origine, la qualité des informations sur les documents enregistrés et non enregistrés, ainsi que les permissions.

**Aucune donnée de production utilisée, aucun nouveau traitement comptable, aucun ajout de modèle ou migration.**