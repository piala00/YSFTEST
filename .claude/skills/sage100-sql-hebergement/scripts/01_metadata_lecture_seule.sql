-- Modèle SQL Server ; exécuter dans la base sélectionnée avec lecture autorisée.
-- Source des vues : MS01. Catalogue attendu : M01 V12.20.
-- Les tables P_ et cbIndice peuvent dépendre de la couche d’accès : vérifier.
WITH attendu(table_attendue, colonne_attendue) AS (
    SELECT * FROM (VALUES
    (N'F_COMPTET', N'CT_Num'),
    (N'F_COMPTET', N'CT_Intitule'),
    (N'F_COMPTET', N'CT_Type'),
    (N'F_COMPTET', N'CG_NumPrinc'),
    (N'F_COMPTET', N'CT_Ville'),
    (N'F_COMPTET', N'CT_Telephone'),
    (N'F_COMPTET', N'CT_EMail'),
    (N'F_COMPTET', N'CT_Sommeil'),
    (N'F_COMPTET', N'CT_Encours'),
    (N'F_COMPTET', N'CT_Assurance'),
    (N'F_COMPTET', N'N_CatTarif'),
    (N'F_COMPTET', N'CT_ControlEnc'),
    (N'F_COMPTEG', N'CG_Num'),
    (N'F_COMPTEG', N'CG_Intitule'),
    (N'F_COMPTEG', N'CG_Type'),
    (N'F_COMPTEG', N'CG_Lettrage'),
    (N'F_ARTICLE', N'AR_Ref'),
    (N'F_ARTICLE', N'AR_Design'),
    (N'F_ARTICLE', N'FA_CodeFamille'),
    (N'F_ARTICLE', N'AR_PrixAch'),
    (N'F_ARTICLE', N'AR_PrixVen'),
    (N'F_ARTICLE', N'AR_UniteVen'),
    (N'F_ARTICLE', N'AR_SuiviStock'),
    (N'F_JOURNAUX', N'JO_Num'),
    (N'F_JOURNAUX', N'JO_Intitule'),
    (N'F_JOURNAUX', N'JO_Type'),
    (N'F_ECRITUREC', N'EC_No'),
    (N'F_ECRITUREC', N'JO_Num'),
    (N'F_ECRITUREC', N'JM_Date'),
    (N'F_ECRITUREC', N'EC_Jour'),
    (N'F_ECRITUREC', N'EC_Date'),
    (N'F_ECRITUREC', N'EC_Piece'),
    (N'F_ECRITUREC', N'CG_Num'),
    (N'F_ECRITUREC', N'CT_Num'),
    (N'F_ECRITUREC', N'EC_Sens'),
    (N'F_ECRITUREC', N'EC_Montant'),
    (N'F_ECRITUREC', N'EC_Norme'),
    (N'F_ECRITUREC', N'EC_CType'),
    (N'F_ECRITUREC', N'EC_Cloture'),
    (N'F_ECRITUREC', N'EC_Impression'),
    (N'P_UNITE', N'U_Intitule'),
    (N'P_UNITE', N'cbIndice'),
    (N'P_CATTARIF', N'CT_Intitule'),
    (N'P_CATTARIF', N'cbIndice')
    ) AS v(table_attendue, colonne_attendue)
)
SELECT a.table_attendue, a.colonne_attendue,
       s.name AS schema_observe, t.name AS table_observee,
       c.name AS colonne_observee, ut.name AS type_declare,
       st.name AS type_systeme, c.max_length AS longueur_octets,
       c.precision AS precision_observee, c.scale AS echelle_observee,
       c.is_nullable, c.collation_name, c.is_identity, c.is_computed,
       CASE WHEN t.object_id IS NULL THEN 'TABLE_ABSENTE_OU_INVISIBLE'
            WHEN c.column_id IS NULL THEN 'COLONNE_ABSENTE_OU_INVISIBLE'
            ELSE 'PRESENTE' END AS constat
FROM attendu AS a
LEFT JOIN sys.tables AS t ON t.name = a.table_attendue
LEFT JOIN sys.schemas AS s ON s.schema_id = t.schema_id
LEFT JOIN sys.columns AS c ON c.object_id = t.object_id
                             AND c.name = a.colonne_attendue
LEFT JOIN sys.types AS ut ON ut.user_type_id = c.user_type_id
LEFT JOIN sys.types AS st ON st.user_type_id = c.system_type_id
                            AND st.system_type_id = c.system_type_id
ORDER BY a.table_attendue, s.name, a.colonne_attendue;
