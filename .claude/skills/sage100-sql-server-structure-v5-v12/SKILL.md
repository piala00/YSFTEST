---
name: sage100-sql-server-structure-v5-v12
description: Utiliser quand Claude doit identifier les tables et champs Sage SQL Server, concevoir le mapping vers un ERP indépendant, préparer des requêtes de lecture, comparer des schémas ou analyser la relation documents/stocks/règlements/comptabilité. Ne jamais inférer que toutes les versions ont le même schéma.
---
# Sage 100 — Dictionnaire SQL Server et contrôle de compatibilité

## Activations et priorité des sources
- Le référentiel est **documentaire** pour V12.20 et **préparatoire** pour V5–V11 et V12.25 ; aucune installation privée n'a été inspectée.
- Lire d'abord `references/RAPPORT_ETAPE_06.md`, puis les CSV pertinents `references/02_CATALOGUE_TABLES.csv`, `03_CHAMPS_REPÈRES.csv`, `04_RELATIONS_DOCUMENTAIRES.csv`, `05_CODES_DOCUMENTS.csv`, `06_ENUMERATIONS.csv`.
- Pour préparer l'inventaire réel, suivre `references/MANUEL_EXTRACTION_POUR_WINDOWS.md` et les scripts `scripts/`.
- Sources Sage référencées dans `references/01_SOURCES.csv` avec version et niveau de vérification. Ne pas affirmer que le manuel V12.25 a été intégralement examiné.

## Règles de résolution obligatoires
1. Demander ou détecter **produit, version majeure, build exact, édition, options et base réellement ouverte** quand une réponse technique exige cette précision. Ne pas confondre V12 et SQL Server 2012.
2. Une table référencée dans un manuel **n'est pas certifiée présente dans toutes les bases**. Les colonnes et schémas doivent être comparés avec les métadonnées de l'installation autorisée.
3. Toute relation de jointure documentée par Sage n'est **pas nécessairement une clé étrangère physique**. Consulter index et sys.foreign_keys avant de déclarer l'existence d'une contrainte.
4. Distinguer `DO_Domaine`, `DO_Type`, `DO_Provenance`, `DO_Valide`, `DO_MajCpta`, `DL_MvtStock`. Ne jamais construire un indicateur CA ou stock à partir d'un seul champ.
5. `F_REGLECH` relie `F_CREGLEMENT` et `F_DOCREGL` : ne pas confondre règlement reçu et imputation effective.
6. Utiliser des requêtes `SELECT` uniquement pour Sage. Toutes écritures métier se font via l'interface ou API/Objets Métiers **version compatibles**, après validation séparée.
7. Toujours préparer des tests de rapprochement avec les états natifs Sage sur des **dossiers de démonstration**, puis marquer la confiance et les limites dans chaque résultat.
8. Ne jamais copier de secrets ou de véritables données commerciales vers la bibliothèque de Skills. Les métadonnées exportées doivent être expurgées de toute information confidentielle.

## Modèle de réponse Claude
Pour une question technique, afficher dans cet ordre :
- **Contexte** : famille Sage / version / édition / base / build ;
- **Réponse sourcée** : table, champs, clé ou jointure avec page, lien ou identifiant de source ;
- **Exemple sûr** : SELECT / méthode de vérification, sans mutation ;
- **Précautions métier** : doubles comptages, statut, stocks, taxes, règlements ;
- **Statut** : DOCUMENTÉ V12.20 / OBSERVÉ SUR INSTALLATION / TESTÉ / NON VÉRIFIÉ ;
- **Tests d'acceptation** : états Sage à comparer avant d'utiliser dans l'ERP.

- Consulter `references/NOTE_VARIATIONS_ET_PRUDENCE.md` pour les variantes de libellés du manuel (dont `DO_Type=12` en achat).

## Étendue des livrables
Ce Skill contient un premier catalogue de tables prioritaires et de champs repères, pas l'ensemble des milliers de champs du manuel Sage. Ne jamais présenter les nombres de lignes du catalogue comme un inventaire exhaustif.


## Complément approfondi étape 06 — Contrôle de sources
- Lire `references/08_TABLES_COMPLEMENTAIRES.csv` (tables supplémentaires par produit et version) puis `references/09_CHAMPS_COMPLEMENTAIRES_VERIFIES.csv` (champs repérés dans les tableaux du manuel V12.20, avec page).
- Index Sage documentaires dans `references/10_INDEX_LOGIQUES_DOCUMENTES.csv`; **pas** de garantie sur les objets `sys.indexes` réellement présents.
- Jointures documentaires dans `references/11_RELATIONS_COMPLEMENTAIRES.csv`; **ne pas les appeler des FK SQL avant preuve `sys.foreign_keys`.**
- Conditions métier et contraintes de driver dans `references/12_REGLES_ET_CONTROLES.csv`; risques dans `references/13_INCONNUES_ET_CONTROLES.csv`.
- Pour comparer V5 à V12 : exécuter sur une base autorisée l'audit des catalogues systèmes `scripts/03_AUDIT_SCHEMA_AVANCE_LECTURE_SEULE.sql`, puis le comparateur CSV `scripts/comparer_exports_structures.py`. Aucun programme n'écrit dans la base Sage.
- Le mot « vérifié » signifie **présence dans le manuel V12.20** et non **observé sur installation**. Les versions V5-V11 ne sont pas attestées par ce complément.
- Toute restitution doit distinguer type et longueur Sage documentaires de type SQL Server physiquement observé; une table `F_` peut porter des champs métier spécifiques selon options et version.
