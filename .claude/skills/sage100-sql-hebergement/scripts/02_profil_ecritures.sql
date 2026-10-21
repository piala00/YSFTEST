-- Modèles de profil SQL Server à adapter au schéma observé (dbo ici).
-- Ne pas lancer avant vérification des tables et colonnes par 01_metadata.
-- Lecture seule ; aucun filtre métier, aucune exclusion de simulation.
-- L'absence de journal reste visible. Les doubles codes parents sont à contrôler.
SELECT e.EC_Norme, e.EC_CType, e.EC_Cloture, j.JO_Type,
       CASE WHEN j.JO_Num IS NULL THEN 1 ELSE 0 END AS journal_orphelin,
       COUNT_BIG(*) AS nombre_lignes,
       SUM(CASE WHEN e.EC_Sens=0 THEN e.EC_Montant ELSE 0 END) AS total_debit,
       SUM(CASE WHEN e.EC_Sens=1 THEN e.EC_Montant ELSE 0 END) AS total_credit,
       SUM(CASE WHEN e.EC_Sens IS NULL OR e.EC_Sens NOT IN (0,1)
                THEN CAST(1 AS bigint) ELSE CAST(0 AS bigint) END) AS sens_inconnu
FROM dbo.F_ECRITUREC AS e
LEFT JOIN dbo.F_JOURNAUX AS j ON j.JO_Num=e.JO_Num
GROUP BY e.EC_Norme, e.EC_CType, e.EC_Cloture, j.JO_Type,
         CASE WHEN j.JO_Num IS NULL THEN 1 ELSE 0 END;

-- Contrôle d'orphelins sans multiplication par les tables parentes.
SELECT COUNT_BIG(*) AS nombre_ecritures,
       SUM(CAST(CASE WHEN j.JO_Num IS NULL THEN 1 ELSE 0 END AS bigint)) AS sans_journal,
       SUM(CAST(CASE WHEN g.CG_Num IS NULL THEN 1 ELSE 0 END AS bigint)) AS sans_compte_detail
FROM dbo.F_ECRITUREC AS e
OUTER APPLY (SELECT TOP (1) j0.JO_Num FROM dbo.F_JOURNAUX AS j0
             WHERE j0.JO_Num=e.JO_Num) AS j
OUTER APPLY (SELECT TOP (1) g0.CG_Num FROM dbo.F_COMPTEG AS g0
             WHERE g0.CG_Num=e.CG_Num AND g0.CG_Type=0) AS g;

-- Unicité préalable aux jointures ; un résultat non vide exige investigation.
SELECT JO_Num, COUNT_BIG(*) AS occurrences FROM dbo.F_JOURNAUX
GROUP BY JO_Num HAVING COUNT_BIG(*) > 1;
SELECT CG_Num, COUNT_BIG(*) AS occurrences FROM dbo.F_COMPTEG
WHERE CG_Type=0 GROUP BY CG_Num HAVING COUNT_BIG(*) > 1;
