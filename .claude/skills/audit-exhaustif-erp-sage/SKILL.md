---
name: audit-exhaustif-erp-sage
description: Inventorier, comparer, tester et corriger chaque commande de tous les logiciels ERP par rapport à Sage 100 V12 et aux spécifications métier propres.
---

# Skill — Audit exhaustif ERP ↔ Sage 100

## Mission
Auditer **sans exception** les boutons, icônes cliquables, menus, sous-menus, actions de listes, dialogues, formulaires, raccourcis et actions conditionnelles de chaque logiciel/module ERP. Comparer les fonctions communes avec **Sage 100 Gestion commerciale et Comptabilité V12** (édition identifiée). Pour les fonctions spécifiques ERP, contrôler la conformité aux spécifications métier. L'objectif est l'équivalence fonctionnelle prouvée, pas la seule ressemblance visuelle.

## Sources de vérité et limites
- ERP : code réel de la branche de référence, tests, templates, JavaScript, routes Django, modèles et services ; navigateur web et bureau en exécution.
- Sage : documentation officielle par produit/version/édition, manuels et preuves sur installation Sage V12. Les sources historiques sont des indices, pas une preuve V12.
- Exiger preuve de chaque comparaison. Si Sage n'est pas disponible, classer A_VERIFIER_SAGE et **ne pas inventer** le comportement.
- Les spécificités transport, multi-agences, SYSCOHADA, reporting et simulation peuvent dépasser Sage ; préserver leur comportement métier.
- Respecter l'intégrité des écritures validées, des stocks, des soldes et des clôtures ; tests uniquement sur données de démonstration.

## Modules à inspecter sans exclusion
Socle et navigation ; accueil ; gestion commerciale ventes, achats, stocks, tiers, articles, tarifs, inventaires, caisse, règlements, états ; comptabilité générale (plan, tiers, journaux, saisie, lettrage, rapprochement, clôtures, SYSCOHADA) ; comptabilité analytique (plans, sections, imputations, balances, grands livres, états) ; reporting, simulations et prévisions ; transport direction, billetterie, colis/courrier, garage, véhicules, propriétaires, agences, caisses ; échanges/synchronisation ; utilisateurs, droits, paramètres, sauvegarde, import/export ; toutes les interfaces web/bureau et autres modules découverts par le dépôt.

## Parcours obligatoire
1. Identifier commit, modules et édition Sage de référence ; dresser un inventaire des fichiers, routes et menus.
2. Extraire toutes les commandes statiques de `apps/core/navigation.py`, templates HTML, JavaScript, URLs et vues ; identifier boutons inactifs, `disabled`, `href="#"`, `TODO`, `pass`, actions sans cible, erreurs JS et fausses confirmations.
3. Exécuter un parcours dynamique des interfaces, chaque rôle, module, sous-module, onglet, fenêtre, statut, contexte, société et agence ; capturer les commandes injectées par JavaScript et les modales.
4. Pour chaque commande, tracer clic → action JS → route/méthode → autorisation serveur → service → transaction → modifications de données → message/édition.
5. Comparer avec Sage par preuve officielle et test sur installation ; consigner écarts de champs, dialogues, règles, droits, enchaînements, stock, comptabilité et traçabilité.
6. Écrire tests positifs/négatifs, cas limites, concurrence, idempotence, permissions, périodes clôturées, documents transformés et multi-agences.
7. Corriger en PR distinctes avec revue croisée ; aucun contournement des contrôles comptables. Retester et reclasser chaque commande.
8. Produire rapport consolidé et métriques **par logiciel et par niveau de preuve** ; terminer uniquement lorsque toutes les commandes ont un statut et que toutes les fonctions requises ont une recette prouvée ou une exception explicitement acceptée.

## Schéma de matrice
`id,logiciel,module,sous_module,onglet,ecran,chemin_menu,libelle,selecteur,source_html,source_js,route,methode_http,vue_service,role,etat_document,condition_activation,fenetre_champs,validation,mutation,stock,comptabilite,analytique,tresorerie,trace,sage_produit,sage_version,sage_edition,preuve_sage,comportement_sage,ecart,gravite,statut,preuve_erp,test,issue,pr,responsable`

## Statuts
`CONFORME_PROUVE`, `ECART_PROUVE`, `INACTIF_VOLONTAIRE`, `INACTIF_ANORMAL`, `NON_IMPLEMENTE`, `A_VERIFIER_SAGE`, `A_TESTER_ERP`, `SPECIFIQUE_ERP`, `NON_APPLICABLE`.

## Priorités
P0 : perte/corruption de données, écriture comptable double ou erronée, sécurité/permissions, stock faux, clôture violée.
P1 : bouton requis absent ou inactif, traitement incomplet, mauvaise fenêtre ou transformation.
P2 : ergonomie, présentation, tri, filtre, impression, libellé et raccourci.

## Critères de réception
Aucun bouton non recensé ; aucune fonction commune déclarée conforme sans preuves Sage et ERP ; aucune action sensible sans tests des permissions et effets serveur ; toutes les anomalies P0/P1 corrigées ou explicitement arbitrées ; résultats reproductibles et liens vers PR/tests. Ne pas confondre inventaire statique, couverture dynamique et conformité prouvée.

## Coordination
Branche GPT séparée ; Claude vérifie et corrige les lots convenus ; consigner dans l'Issue de coordination et les PR. Ne pas écraser les fichiers travaillés simultanément. Ne pas fusionner, déployer ni modifier des données de production sans autorisation.

## Point de départ vérifié (non exhaustif)
`apps/core/navigation.py` contient la navigation commune, avec niveaux de preuve `DOC-V12`, `ERG-CLASSIQUE`, `INDICATIF`, `AJOUT-ERP`. Les routes `apps/commercial/urls.py`, `apps/comptabilite/urls.py` et `apps/transport/urls.py` montrent les circuits métier à parcourir. Inventaire commercial antérieur : 227 commandes terminales de menus et 175 occurrences HTML sur un périmètre limité ; ces chiffres ne décrivent **ni tous les logiciels ni les défauts confirmés**.
