# [GPT] Audit fonctionnel ERP vs Sage 100 V12 — Lot 01

**Date :** 27/10/2026  
**Dépôt :** `piala00/YSFTEST` ; **branche de référence :** `ccr-5592a371-fusjt2`.  
**Objet :** analyser les actions réellement implémentées avant d'attribuer à un bouton un comportement Sage.

## Méthode et limites

Analyse statique de `apps/core/navigation.py`, `static/js/menus.js`, `templates/core/_menu.html`, `templates/commercial/document_list.html`, `templates/commercial/document_detail.html` et `docs/SAGE_V12_POINTS_A_VERIFIER.md`.

- **CODE-VÉRIFIÉ** signifie observé dans les sources de l'ERP, et non testé dans une interface en fonctionnement.
- **SAGE-À-CONFIRMER** signifie qu'aucune source V12 détaillant l'action exacte n'a été vérifiée pour ce constat.
- Le menu Édition porte le niveau de preuve `ERG-CLASSIQUE` dans l'ERP : **ne pas** le renommer `DOC-V12` sans nouvelle source.
- Les éléments `AJOUT-ERP` sont des comportements propres aux deux ERP, non des fonctionnalités Sage démontrées.
- Selon `AGENTS.md`, le nom de Sage figure uniquement dans les documents d'audit, jamais dans les libellés de l'application.

## Matrice de constats

| ID | Fenêtre / commande | Observation dans le code | Risque / suite | Preuve |
|---|---|---|---|---|
| GPT-BTN-001 | Édition › Couper | La version d'origine supprimait la sélection immédiatement après l'appel asynchrone au presse-papiers. | **Corrigé dans cette PR :** pas de suppression tant que la copie n'a pas réussi ; préserver la nouvelle saisie. | CODE-VÉRIFIÉ ; SAGE-À-CONFIRMER |
| GPT-BTN-002 | Édition › Copier | L'API presse-papiers peut manquer ; le code n'explicite pas tous les échecs. | Ajouter gestion d'échec et essais navigateurs. | CODE-VÉRIFIÉ ; SAGE-À-CONFIRMER |
| GPT-BTN-003 | Édition › Ajouter | L'action cherche le premier lien possédant l'icône `bi-plus` ou `bi-plus-square`. | Définir une action contextuelle par écran et vérifier les droits. | CODE-VÉRIFIÉ ; SAGE-À-CONFIRMER |
| GPT-BTN-004 | Édition › Voir/Modifier | L'action prend le premier lien dont l'icône est `bi-pencil`. | Utiliser la fiche réellement sélectionnée, pas une icône. | CODE-VÉRIFIÉ ; SAGE-À-CONFIRMER |
| GPT-BTN-005 | Édition › Supprimer | L'entrée n'a ni URL ni action et apparaît indisponible. | Conserver grisé jusqu'à spécification de la cible et des droits. | CODE-VÉRIFIÉ ; SAGE-À-CONFIRMER |
| GPT-BTN-006 | Liste des documents › Supprimer | Le bouton envoie un POST à `commercial:document_annuler` pour un brouillon. | Clarifier **annulation** versus suppression et impacts métier. | CODE-VÉRIFIÉ ; SAGE-À-CONFIRMER |
| GPT-BTN-007 | Liste des documents › Fonction / Mes filtres | Éléments HTML `span.inactif`, sans fonction. | Recueillir comportement attendu et éditions Sage concernées. | CODE-VÉRIFIÉ ; SAGE-À-CONFIRMER |
| GPT-BTN-008 | Liste des documents › Filtrer | L'action met le focus dans la recherche ; « Plus de critères » révèle statut/dépôt. | Vérifier tri, pagination, filtres sauvegardés et permissions. | CODE-VÉRIFIÉ ; SAGE-À-CONFIRMER |
| GPT-BTN-009 | Fiche document › Comptabiliser | En présence d'une écriture existante, le lien ouvre la fiche de cette écriture, sans comptabiliser à nouveau. | Distinguer consultation et comptabilisation, sans doublon. | CODE-VÉRIFIÉ ; SAGE-À-CONFIRMER |
| GPT-BTN-010 | Édition › Annuler | Utilise `document.execCommand('undo')` sur le dernier champ. | Tests manuels multi-navigateurs requis. | CODE-VÉRIFIÉ ; SAGE-À-CONFIRMER |

## Correctif limité (GPT-BTN-001)

Fichier : `static/js/menus.js`. L'action Couper :
1. refuse un champ désactivé, en lecture seule, sans sélection ou sans presse-papiers disponible ;
2. attend la confirmation de l'écriture dans le presse-papiers ;
3. préserve le contenu si l'écriture échoue ;
4. préserve toute saisie différente effectuée pendant l'attente ;
5. supprime uniquement la sélection d'origine quand la copie réussit.

Tests nouveaux : `tests_js/test_menus_couper.js` (quatre scénarios Node).

## Vérifications et limites d'environnement

- `node --check static/js/menus.js` : réussi localement.
- `node --check tests_js/test_menus_couper.js` : réussi localement.
- `node tests_js/test_menus_couper.js` : **4 scénarios réussis** localement.
- `python manage.py test --parallel 4` : **non exécuté** (Django absent de l'environnement de préparation).
- **Non vérifiés** : navigateurs réels, Windows, autorisations end-to-end, gestion des pièces et comptabilité.

**Demande à Claude Code :** lancer la suite Django complète et la recette web avant approbation ou fusion ; relire les observations, confirmer les comportements Sage avec des sources officielles et répartir les lots suivants. Aucun déploiement, migration ni fusion autorisés par cette PR.
