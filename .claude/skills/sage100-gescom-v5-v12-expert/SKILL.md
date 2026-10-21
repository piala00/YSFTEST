---
name: sage100-gescom-v5-v12-expert
description: "Expertise Sage 100 Gestion Commerciale SQL Server V5–V12 : menus, écrans, champs, commandes, documents, stock, facturation, paramétrage et audit versionné."
---

# Sage 100 Gestion Commerciale SQL Server V5–V12 — Expert et collecte exhaustive

## Principe
Objectif : documenter tous les éléments de chaque version installée, jusqu'aux conditions exactes de boutons et impacts métier. **Le corpus V12 existant est une base de départ, pas une preuve de couverture exhaustive V5–V12.** Lire `references/` et `formations/` hérités de l'ancien Skill V12.

## Références
- Nomenclature Sage V11/V12 : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126081806063
- Tables, champs, valeurs et jointures V12.20 : https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=230113095648937
- Manuels de maintenance et Objets Métiers : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=230113110234020

## Navigation générale
- **Fichier** : dossiers, paramètres société, sécurité, import/export, modèles, outils, maintenance.
- **Édition** : création, modification, suppression, recherche, duplication, navigation.
- **Structure** : fiches articles, familles, nomenclatures, tiers, collaborateurs, dépôts, tarifs, commissions, barèmes, ressources.
- **Traitement** : ventes (devis → commande → livraison → facture/retour/avoir), achats, stocks, inventaire, règlements, fabrication, affaires, abonnements, comptabilisation.
- **État** : clients, fournisseurs, articles, stocks, commercial, marges, palmarès, journaux, tableaux de bord, étiquettes, éditions personnalisées.
- **Fenêtre** : personnalisation, dispositions, colonnes, préférences, barres.
- **?** : aide et assistance.

## Étudier chaque fiche
Lire `references/08-fiches-et-fenetres.md`. Pour toute commande/onglet, relever : chemin complet, édition, options, autorisation, écran, champ, valeurs possibles, valeur par défaut, validation, erreurs, impact stock/compta et code SQL de **lecture** ou objet SDK de **gestion**. Chaque valeur dépendant d'une option est conditionnelle.

## Fonctions critiques et contrôles
1. Types de documents : `DO_Domaine`, `DO_Type` (leurs valeurs exactes sont propres au référentiel et doivent être relevées dans la doc/version). Ne pas confondre retour, BL, facture et commande. Souches propres aux sociétés ne sont pas codes universels.
2. Stock : entrées (+), sorties (−), transferts inter-dépôts (+/−), réservations, valorisation ; les signes exacts de corrections/retours dépendent du type de document et du paramétrage.
3. Tarifs : catégorie, devise, remise, escalier, promotions, remise famille, coûts et TVA ; prouver ordre réel de calcul sur dossier de test.
4. Comptabilisation : preuve de transfert et rapprochement, prévention de doublons, règlements et écritures.
5. Versions V5–V12 : ne jamais transférer une règle ou un champ SQL sans vérification du schéma versionné.

## Extraction et acquisition
- `resources/outils/export_sql_metadata.py` : catalogue réel des tables/champs/index/contraintes de chaque base SQL.
- `resources/outils/capture_ui_windows.py` : contrôles d'accessibilité des fenêtres Windows Sage, sans clic ; demander une capture expurgée lorsque UIA ne fournit pas les libellés.
- `resources/outils/diff_sql_schemas.py` : identifier les évolutions version-à-version.
- Mettre chaque observation dans le schéma unifié, liée à une preuve horodatée.

## Formation
Utiliser les 12 fiches `formations/`, exercices, checklists et modèles. Pour tout cours : contexte, écran, étapes, validation, impact, dépannage, test. **Ne jamais effectuer la démo sur société réelle.**

## Pour projet ERP
Rapprocher chaque vente, facture, avoir et mouvement stock de sa pièce Sage. Ne pas construire le CA par simple somme de tous `F_DOCLIGNE` ; distinguer statut et type de pièce pour éviter double comptage. Lecture seule sur base Sage, synchronisation dans base ERP indépendante, journal technique et reconciliations.
