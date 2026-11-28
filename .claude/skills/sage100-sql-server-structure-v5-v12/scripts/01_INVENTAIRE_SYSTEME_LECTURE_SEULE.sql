/*
Sage 100 / SQL Server — Étape 06. Inventaire de métadonnées uniquement.
NE MODIFIE AUCUNE donnée. À utiliser uniquement sur une base autorisée,
avec un compte SQL dédié au principe du moindre privilège.
Dans SSMS, exécuter séparément chaque SELECT si l'on souhaite exporter les jeux CSV.
Aucune définition de vue ou procédure n'est extraite (évite fuite de secrets).
*/
SET NOCOUNT ON;

-- OBJETS : tables, vues, procédures, déclencheurs et fonctions utilisateur
SELECT SCHEMA_NAME(o.schema_id) AS schema_name, o.name AS object_name,
       o.type_desc AS object_type, o.create_date, o.modify_date
FROM sys.objects AS o
WHERE o.is_ms_shipped = 0 AND o.type IN ('U','V','P','TR','FN','IF','TF')
ORDER BY schema_name, object_type, object_name;

-- COLONNES : métadonnées physiques (aucun enregistrement métier)
SELECT SCHEMA_NAME(t.schema_id) AS schema_name,
       t.name AS table_name, c.column_id AS ordinal,
       c.name AS column_name, ty.name AS sql_type,
       c.max_length, c.precision, c.scale,
       c.is_nullable, c.is_identity, c.is_computed,
       c.collation_name
FROM sys.tables t
JOIN sys.columns c ON c.object_id = t.object_id
JOIN sys.types ty ON ty.user_type_id = c.user_type_id
WHERE t.is_ms_shipped=0
ORDER BY schema_name, table_name, ordinal;

-- INDEX : préserver les clés composites et l'ordre de chaque colonne
SELECT SCHEMA_NAME(t.schema_id) AS schema_name,
       t.name AS table_name, i.name AS index_name,
       i.type_desc AS index_type, i.is_unique, i.is_primary_key,
       ic.key_ordinal, ic.is_included_column, ic.is_descending_key,
       c.name AS column_name
FROM sys.tables t
JOIN sys.indexes i ON i.object_id=t.object_id
JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id
JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
WHERE t.is_ms_shipped=0 AND i.is_hypothetical=0 AND i.name IS NOT NULL
ORDER BY schema_name, table_name, index_name, ic.key_ordinal, c.name;

-- CLÉS ÉTRANGÈRES physiquement présentes (≠ jointures documentaires Sage)
SELECT fk.name AS constraint_name,
       SCHEMA_NAME(tp.schema_id) AS from_schema, tp.name AS from_table,
       cp.name AS from_column, fkc.constraint_column_id AS position,
       SCHEMA_NAME(tr.schema_id) AS to_schema, tr.name AS to_table,
       cr.name AS to_column, fk.is_disabled, fk.is_not_trusted
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id=fk.object_id
JOIN sys.tables tp ON tp.object_id=fkc.parent_object_id
JOIN sys.columns cp ON cp.object_id=tp.object_id AND cp.column_id=fkc.parent_column_id
JOIN sys.tables tr ON tr.object_id=fkc.referenced_object_id
JOIN sys.columns cr ON cr.object_id=tr.object_id AND cr.column_id=fkc.referenced_column_id
ORDER BY constraint_name, position;

-- CHECK / DEFAULT : noms sans copier la définition ni valeurs sensibles
SELECT SCHEMA_NAME(o.schema_id) AS schema_name,
       OBJECT_NAME(cc.parent_object_id) AS table_name,
       cc.name AS constraint_name, 'CHECK' AS constraint_type,
       cc.is_disabled, cc.is_not_trusted
FROM sys.check_constraints cc JOIN sys.objects o ON o.object_id=cc.parent_object_id
UNION ALL
SELECT SCHEMA_NAME(o.schema_id), OBJECT_NAME(dc.parent_object_id), dc.name,
       'DEFAULT', CAST(0 AS bit), CAST(0 AS bit)
FROM sys.default_constraints dc JOIN sys.objects o ON o.object_id=dc.parent_object_id
ORDER BY schema_name, table_name, constraint_name;

-- Dépendances noms d'objets (sans définition SQL)
SELECT SCHEMA_NAME(o.schema_id) AS schema_name, o.name AS referencing_object,
       d.referenced_schema_name, d.referenced_entity_name, d.referenced_id
FROM sys.sql_expression_dependencies d
JOIN sys.objects o ON o.object_id=d.referencing_id
WHERE o.is_ms_shipped=0
ORDER BY schema_name, referencing_object;
