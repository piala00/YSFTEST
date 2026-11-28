# Audit des actions commerciales — lot 04 (Sage 100 V12 vs ERP)

**Périmètre :** 21 types de documents (9 ventes, 9 achats, 3 stocks) ; liste et fiche des documents. **Base :** après fusion PR #2. **Statut :** correctifs proposés et tests ciblés, comparaison officielle partielle ; recette Sage V12 et rôles restent nécessaires.

## Actions désormais reliées dans la liste

| Action liste | Condition d'activation | Fenêtre ou traitement ERP | Effet serveur |
|---|---|---|---|
| Modifier le brouillon | Une pièce \`BROUILLON\` sélectionnée | \`commercial:document_update\` | GET : édition ; POST : mise à jour sous contrôle du serveur |
| Valider la pièce | Une pièce \`BROUILLON\` sélectionnée, confirmation JS | \`commercial:document_valider\` en POST + CSRF | Validation des règles métier, stock/compta selon type, par services existants |
| Choisir une transformation | Une pièce \`VALIDE\` avec types de transformation proposés | Ouvre la fiche, bouton Transformer, **sans POST automatique** | La transformation demeure un POST distinct après sélection de cible |
| Saisir un règlement | Facture valide non avoir, reste dû strictement positif | \`commercial:reglement_create?document=<id>\` | Formulaire lié à la facture ; aucune écriture à l'ouverture |
| Saisir un acompte | Commande client ou fournisseur valide | \`commercial:reglement_create?commande=<id>\` | Formulaire lié à la commande |
| Voir l'écriture comptable | Pièce ayant une écriture liée | \`comptabilite:ecriture_detail\` | Consultation seulement |
| Imprimer | Une pièce sélectionnée | \`commercial:document_print\` | Lecture seule |
| Annuler le brouillon | Une pièce \`BROUILLON\`, confirmation JS | \`commercial:document_annuler\` en POST + CSRF | Annulation traçable, **pas suppression physique** |

La fiche affichait « Comptabiliser » pour une simple ouverture d'écriture déjà existante : le libellé est corrigé. **Pas de deuxième comptabilisation**. Lorsque aucune écriture n'existe, la commande demeure inactive avec une explication.

## Correspondance Sage documentée (preuves limitées)

- [Sage 100 — FAQ Traitements de fin d'année](https://fr-kb.sage.com/portal/app/portlets/results/botviewsolution.jsp?solutionid=211010160106670) distingue **Valider, Valider et imprimer, Comptabiliser** depuis la liste/facture, et mise à jour comptable. Dans notre ERP actuel, \`Document.valider()\` appelle \`comptabiliser_document\` sur les types de facturation. **Différence métier/ergonomique à valider avant d'ajouter une commande de comptabilisation distincte**.
- [Sage 100 — Facture validée et avoir](https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=211010150098707) indique qu'une facture validée erronée doit passer par une facture d'avoir ou de retour, et ne doit pas être réécrite. Ne pas créer une opération « Supprimer la facture validée ».
- [Sage — Ergonomie et fonctions communes](https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=220125200004187) mentionne notamment transformer, imprimer et comptabiliser dans le menu Actions des documents d'achat. **Source ancienne (2016), preuve non spécifique V12**.

Aucune de ces sources ne documente exhaustivement **les dialogues V12 de chaque bouton sur les 21 types, chaque édition et chaque statut**. Leur reproduction fidèle exige des captures/essais sur l'installation Sage V12 de référence.

## Validation demandée à Claude Code

1. Contrôler la sûreté des mutations POST, y compris CSRF, permissions, périodes clôturées, pièces générées et stock négatif ;
2. Recette navigateur « Actions » pour 21 types, statuts de pièce, menus déroulants et fenêtre MDI ;
3. Tests sur copie de données : validation de facture, retour client/fournisseur, avoir, réception, livraison, transfert de stock ;
4. Comparer « Valider et imprimer », « Comptabiliser » et « Transformer » au Sage V12 réel par édition, sans dupliquer les écritures ;
5. Vérifier le passage d'une sélection à l'autre sans laisser activés des boutons invalides.

**Mesures automatiques proposées :** tests Node de l'interface Actions + CI générale Django/SQL Server/Windows. Aucun changement de modèle ou de base, aucun déploiement, aucune fusion sans revue.

**Observation importante :** les restrictions par statut affichées dans HTML/JS ne remplacent PAS les habilitations contrôlées sur les vues Python. Le code serveur existant possède \`@login_required\` et \`@require_POST\` pour certaines routes, mais une revue détaillée des autorisations métier reste requise.
