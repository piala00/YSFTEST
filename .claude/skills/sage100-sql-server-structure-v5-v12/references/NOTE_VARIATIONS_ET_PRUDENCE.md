# Notes de cohérence — Étape 06 (Sage 100 SQL Server)

## Variantes observées dans le manuel V12.20

Dans **Structure des bases Sage 100 V12.20**, la valeur `DO_Type = 12`, domaine achat (`DO_Domaine = 1`), est libellée « Bon de Commande » dans la description de `F_DOCENTETE` et de `F_DOCLIGNE` (pages imprimées 241–242 et 255–256), mais apparaît « Commande confirmée » dans la description d'une table connexe (page imprimée 273). Le catalogue conserve le libellé « Bon de commande » et annote la variation, qui ne doit pas être traitée comme deux codes différents. 

## Deux niveaux à ne jamais confondre

- **Référence documentaire** : l'existence d'une table, d'une colonne ou d'une liaison est mentionnée dans le manuel V12.20.
- **Schéma observé** : l'objet physique a été retrouvé dans `sys.objects`, `sys.columns`, `sys.indexes` ou `sys.foreign_keys` d'une instance autorisée.

Une jointure fonctionnelle publiée n'est pas nécessairement une contrainte FK SQL Server. Le modèle de l'ERP doit stocker ces deux natures de relations séparément.

## Limitations et compatibilité

Cette publication ne décrit **pas** exhaustivement les milliers de colonnes de toutes les installations V5–V12. Le statut `DOCUMENTE_V1220_STRUCTURE` ne permet aucune conclusion automatique sur les builds antérieurs. Les tables peuvent différer selon le produit, l'édition et le paramétrage.

## Conseils de conception

- Pour le chiffre d'affaires, ne pas agréger indistinctement devis, commandes, livraisons et factures.
- Pour les règlements, distinguer règlement saisi, validé, imputé et passé en comptabilité.
- Pour les stocks, distinguer mouvements en quantité, mouvements en valeur, transferts, inventaires et annulations.
- Pour les modifications fonctionnelles, employer l'interface Sage ou un SDK documenté pour la version ; les scripts fournis ne doivent jamais modifier les bases métier.

## Sources principales

- https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=230113095648937
- https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=230113095807277

**Statut :** discordance terminologique identifiée, non résolue par un test utilisateur. Aucune écriture exécutée dans Sage.
