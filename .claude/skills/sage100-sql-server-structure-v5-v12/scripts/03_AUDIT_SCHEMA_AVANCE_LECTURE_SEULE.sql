-- Sage 100 | Audit de schéma SQL Server | LECTURE SEULE, métadonnées uniquement
-- À lancer dans le CONTEXTE DE LA BASE CIBLE autorisée (SSMS : sélectionner la base).
-- Compte avec accès minimum + VIEW DEFINITION selon besoin; ne collecte pas de données métiers.
-- Ne pas lancer sur une base sans autorisation et ne pas exporter de données sensibles.
SET NOCOUNT ON;
-- 1. Tables, vues, procédures, triggers (description des noms seulement)
SELECT DB_NAME() AS base_cible, s.name AS schema_name, o.name AS objet, o.type_desc AS type_objet
FROM sys.objects AS o JOIN sys.schemas AS s ON s.schema_id=o.schema_id
WHERE o.type IN ('U','V','P','TR','FN','IF','TF') ORDER BY s.name,o.name;
-- 2. Colonnes et types SQL réels
SELECT s.name AS schema_name,o.name AS objet,c.name AS colonne,typ.name AS type_sql,
 c.max_length,c.precision,c.scale,c.is_nullable,c.is_identity,c.is_computed
FROM sys.columns AS c JOIN sys.objects AS o ON o.object_id=c.object_id
JOIN sys.schemas AS s ON s.schema_id=o.schema_id
JOIN sys.types AS typ ON c.user_type_id=typ.user_type_id
WHERE o.type IN ('U','V') ORDER BY s.name,o.name,c.column_id;
-- 3. Index physiques et colonnes ordonnées
SELECT s.name AS schema_name,t.name AS table_name,i.name AS index_name,i.is_unique,i.is_primary_key,
 ic.key_ordinal,ic.is_included_column,col.name AS column_name
FROM sys.indexes AS i JOIN sys.tables AS t ON i.object_id=t.object_id
JOIN sys.schemas AS s ON t.schema_id=s.schema_id
JOIN sys.index_columns AS ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id
JOIN sys.columns AS col ON col.object_id=ic.object_id AND col.column_id=ic.column_id
WHERE i.index_id>0 ORDER BY s.name,t.name,i.name,ic.key_ordinal,ic.index_column_id;
-- 4. FK physiques réelles (non les jointures logiques du manuel Sage)
SELECT fk.name AS fk_name,sp.name AS schema_source,tp.name AS table_source,
 cp.name AS colonne_source,sr.name AS schema_cible,tr.name AS table_cible,cr.name AS colonne_cible,
 fkc.constraint_column_id AS ordre_colonne
FROM sys.foreign_keys AS fk JOIN sys.foreign_key_columns AS fkc ON fk.object_id=fkc.constraint_object_id
JOIN sys.tables AS tp ON tp.object_id=fkc.parent_object_id
JOIN sys.schemas AS sp ON sp.schema_id=tp.schema_id
JOIN sys.columns AS cp ON cp.object_id=fkc.parent_object_id AND cp.column_id=fkc.parent_column_id
JOIN sys.tables AS tr ON tr.object_id=fkc.referenced_object_id
JOIN sys.schemas AS sr ON sr.schema_id=tr.schema_id
JOIN sys.columns AS cr ON cr.object_id=fkc.referenced_object_id AND cr.column_id=fkc.referenced_column_id
ORDER BY fk.name,fkc.constraint_column_id;
-- 5. Contraintes uniques, CHECK et défauts (sans contenu SQL ou valeurs)
SELECT s.name AS schema_name,t.name AS table_name,k.name AS nom_contrainte,k.type_desc AS type_contrainte
FROM sys.key_constraints AS k JOIN sys.tables AS t ON t.object_id=k.parent_object_id
JOIN sys.schemas AS s ON s.schema_id=t.schema_id ORDER BY t.name,k.name;
SELECT s.name AS schema_name,t.name AS table_name,dc.name AS default_name,col.name AS column_name
FROM sys.default_constraints AS dc JOIN sys.tables AS t ON t.object_id=dc.parent_object_id
JOIN sys.schemas AS s ON s.schema_id=t.schema_id
JOIN sys.columns AS col ON col.object_id=dc.parent_object_id AND col.column_id=dc.parent_column_id
ORDER BY t.name,col.name;
SELECT s.name AS schema_name,t.name AS table_name,cc.name AS check_name,cc.is_disabled
FROM sys.check_constraints AS cc JOIN sys.tables AS t ON t.object_id=cc.parent_object_id
JOIN sys.schemas AS s ON s.schema_id=t.schema_id ORDER BY t.name,cc.name;
-- 6. Permissions et identité, sans secrets
SELECT DB_NAME() AS base_cible, USER_NAME() AS utilisateur_bdd, ORIGINAL_LOGIN() AS login_initial,
 HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','VIEW DEFINITION') AS a_view_definition,
 HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','SELECT') AS a_select_base;
