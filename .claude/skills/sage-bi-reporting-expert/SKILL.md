---
name: sage-bi-reporting-expert
description: "Expert Sage BI Reporting historique pour Sage 100 : interface Excel, connecteurs, modèles, cubes, listes, paramètres, droits, automate, Player Web/C-S et qualité des indicateurs."
---

# Sage BI Reporting (historique) — architecte du reporting

## Périmètre
Traiter le produit **Sage BI Reporting** historique, orienté Excel et Sage 100, à distinguer de **Sage Business Reporting** SaaS. Sage décrit alimentation Excel **à la cellule, en liste ou en cube**, automatisation tableaux/graphes, connecteurs SQL, contrôle des sources, diffusion via Player C/S, Player Web et Automate (selon options). Source : https://www.sage.com/fr-fr/produits/sage-bi-reporting/.

## Éléments à inventorier par installation
1. Application de paramétrage : sources/connexions, authentification, droits, connecteurs et modèles de données.
2. Interface Excel : onglet(s) Sage du ruban, boutons de mise à jour, listes, cubes, reportings à la cellule, filtres et paramètres ; **intitulés/positions non certifiés sans observation**.
3. États : modèles fournis, vues, feuilles, relations, champs de dimensions/mesures, clés de regroupement, mode calcul.
4. Player : diffusion, lecture avec/sans Excel et permissions distinctes entre consultation/création.
5. Automate (optionnel) : planification, exports PDF, recalculs Excel et distribution mail.
6. Gouvernance : sécurité de sources, jeux d'essai, variables de date, actualisation et traçabilité.

## Analyse métier
- Commercial : CA net par facture sans duplication des BL ; remises, retours, avoirs, transport, TVA, coût, marge.
- Recouvrement : échéances, solde, paiements, retards, affectations et recouvrements.
- Stock : quantité à date, dépôt, coûts, mouvements valorisés, traçabilité inter-magasins.
- Compta : balance, trésorerie, résultat, bilan, répartition analytique, multi-exercices.
- Consolider : multi-agences et devises avec provenance de source, pas d'addition brute des clés identiques.

## Chaque champ de modèle BI
`source → table/vue → champ → filtre → condition → agrégation → unité → règle de date → dimension → sécurité → formule → fréquence → état Sage de réconciliation`. Ne jamais écrire une mesure implicite sans sa définition (ex. CA HT de factures seulement vs BL).

## Livrables
Dictionnaire champs/connecteurs, catalogue modèles, capture annotée ruban Excel, procédures d'actualisation/publication, droits, tests de rafraîchissement/rupture connexion, contrôles de totaux, planning d'automate.

## Limite
Ne pas inventer l'inventaire exact des boutons, champs ou modèles Excel sans capture de la version installée, ses add-ins et ses modèles. Documenter les différences entre BI Reporting local et Business Reporting SaaS.

