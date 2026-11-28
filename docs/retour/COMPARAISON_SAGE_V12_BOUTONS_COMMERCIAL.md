# Audit comparatif des actions — Gestion commerciale ERP OHADA / Sage 100 V12.10

**Date :** 27 octobre 2026  
**Branche de travail :** \`gpt/audit-boutons-sage-v12\`  
**Référence ERP examinée :** \`ccr-5592a371-fusjt2\` (navigation, modèles, vues et templates à la date de l'audit).  
**Statut :** revue de CODE et de DOCUMENTATION ; pas une recette graphique Sage/ERP en fonctionnement.

## A. Sources et niveaux de preuve

1. **Sage, source V12** : [Découpage fonctionnel détaillé Sage 100 Gestion commerciale, fichier V12.10 (2026)](https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=240126080738580). **Preuve de présence et de disponibilité d'une fonctionnalité par édition**, non preuve de l'enchaînement détaillé de chaque clic.
2. **Sage, note de version** : [Découpage Sage 100 V11/V12](https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126081806063) : Sage indique que le découpage V12 est identique à celui de V11.
3. **Sage, présentation commerciale** : [Fiche produit Sage 100 Gestion commerciale](https://www.sage.com/fr-fr/-/media/files/sagedotcom/france/documents/pdf/documentation/fp-sage-100-gestion-commerciale.pdf) : confirme notamment la transformation des pièces sans ressaisie, le suivi facturation et le multidépôt ; ne décrit pas toutes les fenêtres.
4. **Sage, historique non V12** : [Manuel Ergonomie et fonctions communes, version 8.50 (2016)](https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=220125200004187) : détails sur les boutons Actions, listes, fenêtres, menus Édition ; **ne vaut pas preuve de comportement V12** sans confirmation sur l'installation V12.
5. **ERP réel** : \`apps/core/navigation.py\`, \`apps/commercial/models.py\`, \`apps/commercial/views.py\`, \`apps/commercial/urls.py\`, \`templates/commercial/document_{list,detail,form}.html\`, \`static/js/menus.js\`.

**Important :** une occurrence de menu \`DOC-V12\` signifie qu'un intitulé/fonction figure dans un découpage officiel, **pas que l'écran, les colonnes ou le traitement correspondent**. Les fonctions \`ERG-CLASSIQUE\` restent sans preuve V12.

## B. Comparaison initiale des boutons prioritaires

| Priorité | Écran / commande | Source ERP : comportement réellement codé | Sage : ce qui est établi | Statut d'écart et travail à faire |
|---|---|---|---|---|
| P0 | Liste ventes/achats/stocks › Actions | Le menu contient seulement **Imprimer la pièce sélectionnée** et **Actualiser la liste** (\`document_list.html\`). | Le manuel Sage commun historique présente des actions de changement de statut, transformation, impression, comptabilisation et courriel sur la liste d'achats. Le découpage officiel V12 confirme la **gestion du bouton Actions**, pas l'ensemble de chaque option. | **Écart probable important** ; reproduire sur installation V12, selon édition/statut/droits, avant codage. |
| P0 | Fiche pièce › Comptabiliser | Quand \`object.ecriture\` existe, le clic **ouvre la consultation de l'écriture** dans le logiciel comptable. Sinon le bouton est grisé ; une facture est comptabilisée dans \`Document.valider()\`. | La gestion commerciale Sage prévoit la comptabilisation des pièces, mais écran et déclenchement exact V12 à vérifier. | **Confusion de libellé certaine dans l'ERP** : « Comptabiliser » se comporte actuellement comme « Voir l'écriture ». Ne pas créer de double écriture. |
| P0 | Saisie › Valider la pièce | Bouton \`POST\` avec \`name=valider\`, demande confirmation JS puis \`Document.valider()\` : vérification des lignes, règles métier, calcul, numéro, mouvements de stock si concernés et \`comptabiliser_document()\` pour les facturations. | Sage décrit le suivi des ventes, achats et stocks ; le détail des boîtes et contrôles V12 dépend de l'édition et des paramètres. | **Traitement ERP réel** ; tester chaque type de pièce, origine, droit et mutation stock/écriture. |
| P0 | Fiche › Transformer | Le bouton déroulant liste les \`transformations_possibles\` seulement pour une pièce validée ; un \`POST\` crée une **nouvelle pièce en brouillon** en reprenant les lignes et ouvre sa saisie. | Transformation de pièces sans ressaisie établie par fiche produit Sage ; boîtes et options exactes V12 non établies. | **Fonction ERP présente** ; confronter workflow, reprise partielle, pièces et reliquats avec installation Sage V12. |
| P0 | Fiche › Saisir un règlement | Lien en nouvelle fenêtre MDI si pièce facturée valide, non avoir, avec reste dû positif ; la saisie est préliée au document. | Processus de règlement décrit globalement par Sage ; détails d'onglets et d'options V12 non démontrés. | **Conditionnel** ; tester client/fournisseur, paiements partiels, droits, écritures. |
| P0 | Fiche › Saisir un acompte | Pour commandes de ventes/achats validées, ouvre \`reglement_create?commande=...\`. | Échelonnement/acompte disponible selon réglages Sage, à établir par écran V12. | **Conditionnel** ; vérifier circuit acompte puis imputation à la facture. |
| P0 | Liste › Supprimer | Le bouton envoie un \`POST\` vers \`document_annuler\` : **annulation**, jamais suppression physique, et seulement sur brouillon dans cette liste. | Différence V12 entre supprimer et annuler les pièces doit être vérifiée selon le type/statut. | **Ambiguïté certaine du libellé** ; conserver la traçabilité, ne pas supprimer de facture validée. |
| P1 | Document › Fonctions | Bouton déroulant qui rassemble Modifier, Valider, Annuler, Fiche tiers, Règlement/Acompte selon état. | V12 distingue les fonctions contextuelles ; contenu exact du bouton dépend de l'écran/édition/droits. | Reconstituer le menu V12 et comparer statut par statut. |
| P1 | Saisie › Fonctions / Barèmes / Informations / Pied / Imprimer / Comptabiliser / Transformer | Dans \`document_form.html\`, ces **sept éléments sont inactifs** ; l'ajout de ligne, OK, Valider et Annuler ont des traitements. | Certaines fonctions sont disponibles dans la gamme V12, mais pas nécessairement sur tous les types et modes de saisie. | **Écart d'ergonomie à vérifier** (ne pas activer indistinctement des fonctions avec effets métier). |
| P1 | Détail › Barèmes / Pied | Boutons explicitement \`span.inactif\`. | Démonstration écran V12 requise. | Fonctions non développées à recenser par type de pièce. |
| P1 | Liste › Fonction / Mes filtres | Éléments \`span.inactif\`. | Personnalisation et bouton Actions figurent dans les sources Sage ; nombre d'options V12 à relever sur installation. | Inventorier toutes les commandes internes, pas seulement le bouton d'accès. |
| P1 | Liste › Filtrer | Affiche désormais statut/dépôt ; recherche et tri préservés dans la branche GPT. | Critères et fenêtres Sage V12 à relever visuellement. | Premier correctif livré ; tests navigateur et droits encore nécessaires. |
| P1 | Fichier › Nouveau / Ouvrir | Deux entrées de menu sans URL/action, donc grisées. | Découpage V12.10 : Standard sur éditions **On premise** étudiées, indisponibles sur certaines offres Cloud. | Écart selon **édition cible** : ne pas confondre gamme Sage et logiciel multi-société ERP. |
| P1 | Édition › Copier / Coller / Couper / Effacer / Ajouter / Voir-Modifier | Actions dans \`static/js/menus.js\`, lot GPT en PR #2, tests JavaScript ciblés. | Manuel commun Sage version 8.50 : ergonomie générique ; confirmation V12 indispensable. | Relire le comportement des dialogues/champs, accès lecture seule, focus, fenêtre MDI. |

## C. Cartographie technique des dialogues et traitements

| Bouton | Ouverture/interface ERP | Vue ou service exécuté | Mutation potentielle |
|---|---|---|---|
| Nouveau document | Liste → menu déroulant des types propres au domaine → écran de saisie | \`commercial:document_create\` | Pas à l'ouverture ; POST crée brouillon ou valide |
| Modifier | Liste / fiche → fenêtre de saisie | \`commercial:document_update\` | POST seulement en brouillon |
| OK | Même saisie, POST | \`_document_form\` | Enregistre brouillon, lignes, totaux |
| Valider | Confirmation JS / POST / détail pièce | \`document_valider\`, \`Document.valider()\` | Stock / comptabilité selon type et origine |
| Transformer | Menu déroulant / POST / édition de la nouvelle pièce | \`document_transformer\`, \`Document.transformer()\` | Crée une nouvelle pièce en brouillon, traçabilité origine |
| Annuler | Confirmation JS / POST / détail ou liste | \`document_annuler\`, \`Document.annuler()\` | Statut et parfois contre-mouvements stock, contrôle des pièces dérivées |
| Imprimer | Nouvel onglet \`_blank\` / mise en page imprimable | \`commercial:document_print\` | Lecture seule attendue |
| Comptabiliser (fiche) | Ouvre l'écriture déjà existante en nouvelle fenêtre MDI, sinon grisé | \`comptabilite:ecriture_detail\` | **Aucune nouvelle écriture au clic** |
| Saisir un règlement | Nouvelle fenêtre MDI liée à une facture | \`commercial:reglement_create?document=…\` | POST de règlement, imputation/écriture selon métier |
| Saisir un acompte | Nouvelle fenêtre MDI liée à une commande | \`commercial:reglement_create?commande=…\` | POST d'acompte, rattachement ultérieur |
| Informations | Panneau d'informations repliable dans la fiche | JS lié à \`piece-informations\` | Lecture seule attendue |
| Ajout de ligne | Ajoute une ligne au formulaire dynamique | \`document_form.html\` + JS | Modification du brouillon lors du POST |
| Suppr. ligne | Champ \`f.DELETE\` géré par formset Django | \`LigneDocumentFormSet\` | Supprime une ligne du brouillon au POST |

## D. 21 types et 84 scénarios de base

Le modèle \`Document\` définit **9 ventes + 9 achats + 3 stocks**. Chaque type est étudié avec **4 statuts** (\`BROUILLON\`, \`VALIDE\`, \`TRANSFORME\`, \`ANNULE\`) = **84 scénarios théoriques**. Certains couples ne seront jamais atteints dans les règles métier : ce n'est pas un inventaire de 84 écrans réellement accessibles.

La matrice générée \`docs/retour/MATRICE_ACTIONS_DOCUMENTS_COMMERCIAL.csv\` détaille par couple type/statut :
- les commandes déclarées, celles conditionnelles et les fonctions inactives ;
- les cibles de transformation ;
- l'effet potentiel sur le stock et la comptabilisation ;
- le statut des preuves Sage V12 et des tests ERP.

**Limites de preuve :** aucun clic dans une installation Sage V12 n'a encore été effectué dans cette PR. Le lien/document Sage officiel n'est pas un remplacement de la capture ou de la recette par édition. L'ERP n'a pas été testé en navigation réelle par ce document.

## E. Travail à répartir immédiatement avec Claude

- **Claude — vérification Sage :** comparer les menus V12.10 et les fenêtres réellement visibles, toutes éditions/permissions retenues, boutons internes aux menus déroulants, états par type de pièce ; annoter les sources, captures, pages.
- **GPT — inventaire/code :** maintenir \`recenser_boutons_commercial\`, les 3 fichiers CSV/MD, relier chaque action à ses URLs/vues et rédiger les tests de non-régression.
- **Claude — métier :** contrôler l'ordre des opérations stock, comptabilité, annulation/avoir, documents d'origine, règlements et transformations ; tester sur données de démonstration.
- **Revue croisée :** aucune fusion avant validation CI Linux/SQL Server/Windows et preuve des écarts.

**Périmètre restant :** formulaires rendus dynamiquement, fenêtre de sélection/impression, fonctions de la barre verticale et boîtes Bootstrap/JS générées, profils utilisateurs et données multi-sociétés, Sage édition Premium V12 testée. Le chiffre de 402 occurrences statiques ne prétend pas les couvrir intégralement.
