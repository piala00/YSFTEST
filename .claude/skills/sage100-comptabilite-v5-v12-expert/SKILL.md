---
name: sage100-comptabilite-v5-v12-expert
description: "Comptabilité Sage 100 SQL Server V5–V12 : interface, écritures, comptes, tiers, analytique, règlements, journaux, états et sécurité."
---

# Sage 100 Comptabilité SQL Server V5–V12 — expert fonctionnel et technique

## Mission
Enseigner et auditer **tous** menus/fenêtres/champs/états/comportements de la version concrète. Commencer par l'inventaire officiel V11 compatible V12 : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126081806063. Le contenu ci-dessous est un **référentiel des familles de fonctions**, pas une liste exhaustive de tous les onglets.

## Menus de référence
**Fichier** : dossier, paramètres société, informations, droits, import/export, sauvegarde, maintenance, outils et configuration.
**Édition** : ajouter, modifier, supprimer, dupliquer, rechercher, navigation, copier/coller, personnalisation selon version.
**Structure** : Plan comptable (comptes généraux), plan tiers, plan analytique, plans reporting, codes journaux, taxes, modes de règlement, banques et RIB, modèles de saisie, exercices, sections analytiques, budgets, informations libres (vérifier édition).
**Traitement** : Journaux de saisie et saisie d'écritures, interrogation et lettrage, pointage, rapprochement bancaire, gestion des extraits, saisie par lot, saisie analytique, régularisations, abonnements, rappels/relevés, transfert, clôture périodique et fin d'exercice (selon édition et version).
**État** : Brouillards, journaux, grand livre, balances, balance âgée, états tiers, échéanciers, états analytiques, bilan, compte de résultat, déclarations de taxes, états budgétaires, révision et états personnalisés.
**Fenêtre / ?** : affichage, préférences, listes, barres, aide.

## Tables Sage 100 Comptabilité documentées officiellement (exemples)
`F_COMPTEG` comptes généraux; `F_COMPTET` tiers; `F_COMPTEA` analytique; `F_ECRITUREC` écritures comptables; `F_JOURNAUX` codes journaux (à contrôler localement), `F_COMPTETG` liens tiers/comptes généraux; `F_COMPTEGBUDGET` budget général. Lire toutes les définitions et jointures dans https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=230113095648937, section Comptabilité pp. 14–150 (pagination interne) et jointures à partir de p. 401.

## Pour CHAQUE fenêtre/onglet
Enregistrer : chemin exact, version, famille, nature, droit d'accès, champ, type/longueur/valeurs, saisie obligatoire, valeurs générées, type de contrôle, changement d'état, validations et rétroactions. **Ne pas déduire un champ UI de sa seule existence SQL**. Associer tout champ démontré à la fiche de catalogue.

## Séquence pédagogique
1. Paramètres de société, exercice, plan et journaux.
2. Création de tiers, comptes, taxes, sections, banques.
3. Saisie et rectification des écritures, contrôle débit=crédit, pièce unique et journal daté.
4. Lettrage, délettrage, rapprochement bancaire, échéances, devises, règlements.
5. Analytique, budgets, consolidation, reporting.
6. États : grand livre, balances, journaux, tiers, bilan, résultat ; rapprocher chiffres.
7. Fin de période/exercice, reports à nouveau, archivage et contrôle ; sauvegarder en labo.
8. Diagnostiquer erreurs, droits et incohérences entre modules.

## Contrôles pour ERP
- Écriture : journal, date, compte, tiers, pièce, exercice, montant débit/crédit, devise, lettrage, section analytique, provenance, transfert Gescom et non-duplication.
- Reconstituer soldes d'ouverture + mouvements, compte/tiers/exercice/période ; ne pas assimiler grand livre à cumul simpliste sans reports et clôtures.
- Pour systèmes OHADA : utiliser le plan local validé, paramétrage entreprise et règles fiscales camerounaises confirmées ; ne pas imposer les modèles français par défaut.
- Réconciliation : balance, bilan, tiers, écritures imputées, taxes ; conserver preuves de l'état Sage édité.
- SQL lecture seule ; écritures autorisées via SDK/Sage si l'édition et le scénario le permettent.

## Sources
- Arborescence des menus Compta et édition : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126081806063
- Dictionnaire tables/champs/jointures : https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=230113095648937
- Manuels techniques : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=230113110234020

## Exigence d'exhaustivité
Pour V5–V12 : utiliser captures de chaque installation, comptes de formation aux droits définis, export SQL metadata et test des comportements. Dans le catalogue, afficher les inconnus, ne pas les compléter au jugé.

