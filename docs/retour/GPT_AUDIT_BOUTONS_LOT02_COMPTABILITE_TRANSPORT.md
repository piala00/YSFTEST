# Audit ERP ↔ Sage 100 V12 — Lot 02 : comptabilité et transport

Date : 2026-10-27. Référence : branche `ccr-5592a371-fusjt2`.
**Niveau de preuve : inspection statique des fichiers `apps/core/navigation.py`, `apps/comptabilite/urls.py`, `apps/transport/urls.py`, `apps/commercial/urls.py` et de l'inventaire historique. Aucune recette navigateur, exécution de tests ni comparaison sur installation Sage V12 dans ce lot.**

## Résultats vérifiables

1. La matrice `docs/retour/MATRICE_AUDIT_GLOBAL_ERP_SAGE.csv` ne contient que son en-tête : **blocage de traçabilité P1**. Ne déclarer aucune couverture complète.
2. La navigation comptable expose `Fichier > Nouveau`, `Ouvrir`, `Favoris` sans URL ni action : commandes grisées par construction (`Element` et `E`). **P1, NON_IMPLEMENTE dans la navigation** ; vérifier les alternatives métier avant d'exiger un correctif.
3. La navigation comptable expose `Paramètres société > Identification > Monnaie & Formats`, `Préférences`, `Reports à-nouveaux`, `Sécurité` sans URL ni action : **P1, NON_IMPLEMENTE dans la navigation**, non preuve d'absence totale de fonctionnalité.
4. `Fichier > Importer` et `Exporter` de la comptabilité n'ont ni URL ni action dans `menu_fichier_comptabilite()` : **P1, NON_IMPLEMENTE dans la navigation**. Les procédures d'import/export réelles doivent être recherchées ailleurs.
5. `Édition > Supprimer`, `Dupliquer`, `Précédent`, `Suivant` n'ont ni URL ni action dans `menu_edition()`. **P1, NON_IMPLEMENTE dans la navigation**, vérifier les écrans et raccourcis contextuels.
6. `Fenêtre > Personnaliser les écrans`, `Personnaliser la liste`, `Ajustement automatique des colonnes` n'ont ni URL ni action dans `menu_fenetre()` : **P2, NON_IMPLEMENTE dans la navigation**.
7. Comptabilité : routes déclarées pour `ecriture_valider`, `ecriture_supprimer`, `delettrage`, `lettrage_auto`, `cloture_exercice`, `cloture_journaux`. **P0 à tester** : POST obligatoire, permission serveur, période clôturée, équilibre débit/crédit, double soumission, journalisation ; aucune anomalie prouvée par la seule présence de routes.
8. Transport : routes déclarées pour `billet_vente`, `depart_form`, `cloture_journee`, `transferts`, `colis_form`, `depense_form`. **P0 à tester** : permissions, caisse/service/agence, unicité billet et siège, idempotence, transferts internes, écritures et annulations ; aucune anomalie prouvée.
9. Commercial : routes déclarées pour `document_valider`, `document_transformer`, `document_annuler`, `stock_comptabiliser`, `reglement_rattacher`. **P0 à tester** : stock, comptabilité, statut, document source, double clic, agences et transactions.
10. Les neuf types de documents vente, neuf achat et trois stock partagent des écrans génériques. **P1** : tester séparément chaque type, statut et rôle, y compris les boutons contextuels. Ne pas multiplier les occurrences de templates par 21 pour annoncer un total de boutons.

## Référence Sage

La source du code `navigation.py` mentionne un découpage Sage V11/V12 et distingue `DOC-V12`, `ERG-CLASSIQUE`, `INDICATIF`, `AJOUT-ERP`. Ces étiquettes ne prouvent pas une équivalence fonctionnelle. Les éléments ci-dessus sont **A_VERIFIER_SAGE** tant que le comportement n'est pas étayé par une source officielle précise et une recette V12. Les fonctions Transport propres à l'ERP sont **SPECIFIQUE_ERP**, à confronter aux spécifications Transport et non à un faux équivalent Sage.

## Plan de recette priorisé

- **P0 — Comptabilité** : valider/supprimer écritures, lettrage/délettrage, clôtures ; tester refus GET, droits, agence/société, transactions, écritures équilibrées et périodes clôturées.
- **P0 — Transport** : vente de billet, clôture par service et agence, transferts de caisse, colis, dépenses ; tester doublons, rapprochement et consolidation sans double comptage.
- **P0 — Commercial** : validation, transformation et annulation de chaque type de document ; impacts stock, comptabilité et règlements.
- **P1 — Navigation** : décider pour chaque commande grisée si elle doit être implémentée, redirigée vers un écran existant ou explicitement déclarée hors périmètre ; tests du clic réel.
- **P1 — Matrice** : créer une ligne par commande et contexte, avec route, rôle, état, preuve ERP, preuve Sage, résultat et ticket ; ne pas laisser les champs de preuve inventés.
- **P2 — Ergonomie** : personnalisation des colonnes, raccourcis, modales, impression.

## Conditions de clôture du lot

Les dix constats sont des **observations statiques / hypothèses de recette**, pas des bugs runtime confirmés. Claude doit ajouter les preuves de navigateur, les tests automatisés, les liens de correctifs et les références officielles Sage avant de classer CONFORME_PROUVE ou ECART_PROUVE. Travail uniquement sur base de démonstration ; pas de fusion, déploiement ou écriture en production.
