# [GPT] Audit boutons ERP Commercial / Transport — lot 02

**Date :** 27 octobre 2026  
**Auteur :** ChatGPT / GPT  
**Branche :** `gpt/audit-boutons-sage-v12` ; PR #2 vers `ccr-5592a371-fusjt2`.

## 1. Objet : accélérer sur les comportements, pas seulement les libellés

Ce lot corrige des actions **réellement présentes dans le code**. Il n'affirme pas reproduire exactement toutes les fenêtres Sage 100 V12 ; celles-ci nécessitent les captures et les preuves recensées dans `docs/SAGE_V12_POINTS_A_VERIFIER.md`.

Deux niveaux de preuve :
- **ERP/code vérifié** : observation dans les fichiers du projet et, si indiqué, test JavaScript automatisé ;
- **Sage/source officielle** : documentation éditeur explicitement citée, sans déduire les champs ou comportements non présentés.

### Sources officielles Sage à confronter à la version installée

1. [Sage — Découpage fonctionnel détaillé](https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126081806063) : la documentation précise que le découpage fonctionnel V12 est celui de V11, mais cela **ne documente pas tous les clics ni les raccourcis de l'interface**.
2. [Sage — FAQ traitements de fin d'année](https://fr-kb.sage.com/portal/app/portlets/results/botviewsolution.jsp?solutionid=211010160106670) : indique distinctement les actions « Valider », « Valider et imprimer » et « Comptabiliser » depuis les listes, documents ou traitements. La facturation OHADA et les paramètres de l'ERP ne doivent pas être inférés de cette FAQ.
3. `docs/AUDIT_SAGE_V12_GESCOM.md` et `docs/SAGE_V12_POINTS_A_VERIFIER.md` : inventaire du projet ; les éléments marqués `ERG-CLASSIQUE` restent à vérifier sur une installation V12.

## 2. Grille des boutons et du comportement actuel

| Bouton/commande | État avec ce lot | Fichier | Preuve et restriction |
|---|---|---|---|
| Édition › Couper | **Corrigé** : suppression du texte seulement après copie réussie ; saisie récente préservée | `static/js/menus.js` | Test Node ciblé |
| Édition › Copier | **Corrigé** : gestion API absente, refus explicite, sélection conservée | `static/js/menus.js` | Test Node ciblé |
| Édition › Coller | **Corrigé** : refus champ protégé ou non textuel, attente asynchrone sans écraser la saisie | `static/js/menus.js` | Test Node ciblé |
| Édition › Effacer | **Corrigé** : respect des champs protégés, suppression limitée à la sélection | `static/js/menus.js` | Test Node ciblé |
| Édition › Ajouter | **Amélioré** : action explicite de la fenêtre avant recherche par icône ; sur les documents ouvre le choix de type | `static/js/menus.js`, `document_list.html` | Test Node ciblé ; repli ancien conservé pour les autres écrans |
| Édition › Voir/Modifier | **Amélioré** : ouvre le document sélectionné ou le lien Modifier de la pièce active ; repli ancien conservé ailleurs | `static/js/menus.js`, templates | Test Node ciblé ; serveur responsable des droits |
| Fichier › Imprimer / barre | **Amélioré** : la liste imprime uniquement la pièce sélectionnée ; la fiche ouvre son impression | `static/js/menus.js`, templates | Test Node ciblé ; impression navigateur des autres pages inchangée |
| Liste › Ouvrir | **Amélioré** : sélection obligatoire, état visuel et clavier | `document_list.html` | Contrôle statique ; recette navigateur requise |
| Liste › Nouveau | **Amélioré** : ouvre les types de pièces existants, ne choisit pas arbitrairement un type | `document_list.html` | Contrôle statique ; aucun nouveau type inventé |
| Liste › Filtrer | **Corrigé** : expose les critères statut/dépôt plutôt que de ne cibler que la recherche | `document_list.html` | Contrôle statique ; recette de filtres à faire |
| Liste › Plus de critères | **Conservé** : masque/révèle les critères | `document_list.html` | Code vérifié |
| Liste › Supprimer | **Sécurisé** : l'action existante d'**annulation** refuse une pièce hors brouillon côté client ; POST + CSRF conservés | `document_list.html` | Côté serveur, règles métier et habilitations toujours prioritaires |
| Liste › Imprimer | **Corrigé** : commande grisée sans ligne sélectionnée | `document_list.html` | Test Node ciblé |
| Liste › Fermer | **Conservé** : ferme la fenêtre interne ou navigue dans l'historique | `document_list.html` | Code vérifié |
| Fiche › Imprimer | **Relié** au menu générique Imprimer | `document_detail.html` | Contrôle statique |
| Fiche › Modifier | **Relié** à la fenêtre active si la pièce est modifiable | `document_detail.html` | Contrôle statique |
| Fiche › Comptabiliser | **À préciser** : le lien actuel ouvre l'écriture existante, il ne lance pas la comptabilisation | `document_detail.html` | Une fonction distincte nécessite audit de validation/permissions |
| Liste › Fonction / Mes filtres | **Non développé** : éléments encore inactifs | `document_list.html` | Ne pas inventer options Sage sans preuve |
| Édition › Supprimer / Dupliquer | **Non développé** en menu générique ; l'annulation par liste est distincte | `apps/core/navigation.py` | Ne pas rendre destructif sans règle métier prouvée |

## 3. Tests exécutés sur GitHub

Workflow `.github/workflows/audit-boutons.yml` ajouté sur la branche GPT :
- syntaxe de `static/js/menus.js` et des fichiers de test ;
- **4 scénarios** de `Couper` ;
- **12 contrôles** pour `Copier`, `Coller`, `Effacer`, les commandes contextuelles et les marqueurs de page.

Exécution GitHub Actions : https://github.com/piala00/YSFTEST/actions/runs/40464878511 — **réussie** (premier run de ce lot).

**Non exécutés pour validation fonctionnelle** : suite Django complète, tests navigateur réel, SQL Server et tests Windows ; les jobs plus larges de `Contrôle` peuvent être en cours ou échouer indépendamment. Cette PR reste **brouillon** jusqu'à leur vérification.

## 4. Suites prioritaires à confier à GPT / Claude

1. Examiner les actions commerciales `Valider`, `Valider et imprimer`, `Transformer`, `Comptabiliser`, `Règlement`, avec statut, écritures, stocks et habilitations (la documentation Sage distingue ces opérations).
2. Implémenter, si validé, les fonctions `Fonction` et `Mes filtres` sur la liste documentaire, avec persistance **par utilisateur** plutôt qu'un stockage commun au navigateur.
3. Remplacer progressivement les derniers choix par icône par des actions déclaratives sur les **fiches clients, fournisseurs, articles, journaux et écritures** ; un écran = une action explicitement définie.
4. Obtenir captures Sage **V12 et édition exacte**, statut de document et droits utilisateur ; marquer chaque comportement « documentation », « installation constatée », « proposé ERP » ou « à confirmer ».
5. Vérifier en particulier la différence entre l'annulation et la suppression d'une pièce : pas d'effacement d'écriture validée ou de conséquence de stock sans traçabilité.

**Ne pas fusionner, migrer de données ni déployer sans validation du propriétaire.**
