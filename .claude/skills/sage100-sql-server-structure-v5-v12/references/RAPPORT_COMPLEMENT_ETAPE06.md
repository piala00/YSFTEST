# Étape 06 — Complément approfondi structures SQL Sage 100

Date : 21 octobre 2026. **Toujours l'étape 06, aucune étape 07 entamée.**

## Objet
Augmenter le catalogue de l'étape 06 sans inventer les champs de V5 à V11 ni revendiquer une exploration d'installations privées.

## Réalisations nouvelles (par rapport au catalogue original)
- **148 entrées produit/table** supplémentaires extraites des pages PDF index 4–12 du manuel Sage V12.20 (on conserve les distinctions COMPTA/GESCOM).
- **134 références table/champ** supplémentaires dans les pages PDF 195–275; chacune a son nom exact et sa page. Les champs déjà présents dans le catalogue initial ont été dédupliqués.
- **30 descriptions d'index logiques** du manuel (sans les supposer matérialisés en SQL Server).
- **49 liens documentaires** de tables, issus des pages 405–419 (sans les qualifier automatiquement de FK physiques).
- **20 règles, comportements ou précautions** concernant stocks, champs obligatoires, lots/gammes, échéances, dépôt, pièces et intégration.
- Script T-SQL d'**audit des métadonnées** (tables, vues, colonnes, contraintes, index, FK, métadonnées de procédures et triggers). Il n'interroge que `sys.*`.
- Comparateur de deux exports CSV, testé sur fixtures et détectant AJOUT, RETRAIT et MODIFICATION.

## Apports techniques majeurs

### Stocks
La table `F_ARTSTOCK` représente une granularité article × dépôt (`AR_Ref`, `DE_No`), avec quantités de stock, réservées, commandées, préparées et contremarque qui ne sont pas interchangeables. `F_ARTSTOCKEMPL` rajoute la granularité emplacement. Le manuel décrit des limitations du driver Sage sur les modifications de certaines colonnes. **La règle ERP reste : jamais d'écriture SQL métier directe.**

### Index et jointures
L'index documentaire `IAR_REF` et l'index `IAS_REF` sont décrits par Sage. Mais ces noms et propriétés ne signifient pas qu'une table possède telle PK ou telle FK SQL en exploitation : vérifier `sys.indexes`, `sys.index_columns`, `sys.key_constraints`, `sys.foreign_keys` et `sys.foreign_key_columns`.

### Comptabilité
Relier les écritures `F_ECRITUREC` à leurs journaux, comptes généraux et tiers sans supposer que les chiffres de Gestion Commerciale coïncident automatiquement avec les chiffres comptabilisés. Les exceptions, écritures clôturées et liaisons avec règlements doivent être testées.

### Échéances et règlements
`F_DOCREGL` comprend une ligne d'équilibrage gérée par la couche Sage; `F_REGLECH` documente la liaison entre règlement et échéance. Une date de règlement n'est pas un indice suffisant de son imputation.

## Sources et validation
- Sage (juillet 2026), *Sage 100 V12.20 — Structure des bases* : https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=230113095648937
  - catalogue tables pages PDF 4–12;
  - champs et index pages PDF 195–275;
  - relations pages PDF 405–419.
- Microsoft Learn, vues des catalogues SQL Server : https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/object-catalog-views-transact-sql?view=sql-server-ver16
- Microsoft Learn, visibilité des métadonnées: https://learn.microsoft.com/en-us/sql/relational-databases/security/metadata-visibility-configuration?view=sql-server-ver16

Statut des entrées : **DOCUMENTÉ V12.20**, non **OBSERVÉ V12 installé**. Le manuel V12.25 et toutes les bases V5–V11 restent en attente de preuves.

## Limites explicites
1. Les catalogues complémentaires ne reprennent **pas tous** les milliers de champs Sage; seulement les zones effectivement examinées et extraites au cours de ce lot.
2. Certaines tables figurent dans plusieurs types de bases Sage. Utiliser `produit + table` et vérifier l'installation.
3. Les relations du manuel n'impliquent pas toutes des clés étrangères SQL physiques.
4. Les colonnes « en lecture/écriture » du manuel s'appliquent au **driver Sage**, pas à une licence de modifier SQL directement.
5. La sécurité de la connexion SQL relève des **privilèges** effectifs, pas simplement d'`ApplicationIntent=ReadOnly`.
6. Les requêtes d'inventaire ne détecteront que les métadonnées visibles par le compte d'audit.
7. La couverture des règles de calcul du chiffre d'affaires, des stocks et du recouvrement n'est pas certifiée avant rapprochement avec des états Sage d'un environnement de test.

## Décision
Complément documentaire terminé, **étape 06 non validée automatiquement**. Attendre décision de l'utilisateur avant étape 07.
