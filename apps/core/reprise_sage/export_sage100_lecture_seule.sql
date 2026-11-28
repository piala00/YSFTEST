/* EXPORT SAGE 100 SQL SERVER → ERP OHADA — LECTURE SEULE (uniquement des SELECT)
   Exécutez chaque requête et enregistrez la grille dans le fichier CSV indiqué (avec l'en-tête).
   Si une colonne « À CONFIRMER » n'existe pas dans votre version, retirez-la de la requête.
   Choisissez soit soldes.csv (soldes d'ouverture), soit ecritures.csv + analytique.csv (détail). */

-- depots.csv  (F_DEPOT)
SELECT DE_No, DE_Intitule, DE_Principal, DE_Ville FROM dbo.F_DEPOT ORDER BY DE_No;

-- familles.csv  (F_FAMILLE)
SELECT FA_CodeFamille, FA_Intitule, FA_Type FROM dbo.F_FAMILLE ORDER BY FA_CodeFamille;

-- comptes.csv  (F_COMPTEG)
SELECT CG_Num, CG_Intitule, CG_Type FROM dbo.F_COMPTEG ORDER BY CG_Num;

-- journaux.csv  (F_JOURNAUX)
SELECT JO_Num, JO_Intitule, JO_Type, CG_Num FROM dbo.F_JOURNAUX ORDER BY JO_Num;

-- sections.csv  (F_COMPTEA)
SELECT N_Analytique, CA_Num, CA_Intitule, CA_Type, CA_Sommeil FROM dbo.F_COMPTEA ORDER BY N_Analytique;

-- taxes.csv  (F_TAXE)
SELECT TA_Code, TA_Intitule, TA_Taux, TA_Sens, CG_Num FROM dbo.F_TAXE ORDER BY TA_Code;

-- tiers.csv  (F_COMPTET)
SELECT CT_Num, CT_Intitule, CT_Type, CG_NumPrinc, CT_Ville, CT_Telephone, CT_EMail, CT_Sommeil, CT_NumPayeur, N_CatTarif, CT_Encours FROM dbo.F_COMPTET ORDER BY CT_Num;

-- articles.csv  (F_ARTICLE)
SELECT AR_Ref, AR_Design, FA_CodeFamille, AR_SuiviStock, AR_Sommeil, AR_PrixAch, AR_PrixVen FROM dbo.F_ARTICLE ORDER BY AR_Ref;

-- tarifs.csv  (F_ARTCLIENT)
SELECT AR_Ref, AC_Categorie, AC_PrixVen, CT_Num FROM dbo.F_ARTCLIENT ORDER BY AR_Ref;

-- stocks.csv  (F_ARTSTOCK)
SELECT AR_Ref, DE_No, AS_QteSto, AS_MontSto, AS_QteMini, AS_QteMaxi FROM dbo.F_ARTSTOCK ORDER BY AR_Ref;

-- soldes.csv  (F_ECRITUREC)
SELECT e.CG_Num, ISNULL(e.CT_Num, '') AS CT_Num, SUM(CASE WHEN e.EC_Sens = 0 THEN e.EC_Montant ELSE 0 END) AS Debit, SUM(CASE WHEN e.EC_Sens = 1 THEN e.EC_Montant ELSE 0 END) AS Credit FROM dbo.F_ECRITUREC AS e LEFT JOIN dbo.F_JOURNAUX AS j ON j.JO_Num = e.JO_Num WHERE DATEADD(day, e.EC_Jour - 1, e.JM_Date) BETWEEN '20260101' AND '20261231' AND e.EC_Norme IN (0, 1) AND (j.JO_Type IS NULL OR j.JO_Type <> 4) GROUP BY e.CG_Num, ISNULL(e.CT_Num, '') ORDER BY e.CG_Num, CT_Num;

-- ecritures.csv  (F_ECRITUREC)
SELECT e.EC_No, e.JO_Num, CONVERT(char(10), DATEADD(day, e.EC_Jour - 1, e.JM_Date), 23) AS EC_DateCompta, e.EC_Piece, e.CG_Num, e.CT_Num, e.EC_Sens, e.EC_Montant, e.EC_Intitule, e.EC_Lettrage FROM dbo.F_ECRITUREC AS e LEFT JOIN dbo.F_JOURNAUX AS j ON j.JO_Num = e.JO_Num WHERE DATEADD(day, e.EC_Jour - 1, e.JM_Date) BETWEEN '20260101' AND '20261231' AND e.EC_Norme IN (0, 1) AND (j.JO_Type IS NULL OR j.JO_Type <> 4) ORDER BY e.JO_Num, e.JM_Date, e.EC_Piece, e.EC_No;

-- analytique.csv  (F_ECRITUREA)
SELECT a.EC_No, a.N_Analytique, a.CA_Num, a.EA_Montant FROM dbo.F_ECRITUREA AS a JOIN dbo.F_ECRITUREC AS e ON e.EC_No = a.EC_No LEFT JOIN dbo.F_JOURNAUX AS j ON j.JO_Num = e.JO_Num WHERE DATEADD(day, e.EC_Jour - 1, e.JM_Date) BETWEEN '20260101' AND '20261231' AND e.EC_Norme IN (0, 1) AND (j.JO_Type IS NULL OR j.JO_Type <> 4) ORDER BY a.EC_No;

-- documents.csv  (F_DOCENTETE)
SELECT DO_Domaine, DO_Type, DO_Piece, DO_Date, DO_Tiers, DO_Ref, DE_No, DO_Provenance, CT_NumPayeur FROM dbo.F_DOCENTETE AS x WHERE x.DO_Domaine IN (0, 1, 2) AND x.DO_Type NOT IN (8, 18, 22, 24, 25, 26, 27) AND (x.DO_Date >= '20260101' OR x.DO_Type IN (0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15) OR EXISTS (SELECT 1 FROM dbo.F_DOCREGL r WHERE r.DO_Domaine = x.DO_Domaine AND r.DO_Type = x.DO_Type AND r.DO_Piece = x.DO_Piece AND r.DR_Regle = 0)) ORDER BY DO_Domaine, DO_Type, DO_Piece;

-- lignes.csv  (F_DOCLIGNE)
SELECT l.DO_Domaine, l.DO_Type, l.DO_Piece, l.DL_No, l.DL_Ligne, l.AR_Ref, l.DL_Design, l.DL_Qte, l.DL_MontantHT, l.DL_MontantTTC FROM dbo.F_DOCLIGNE AS l WHERE EXISTS (SELECT 1 FROM dbo.F_DOCENTETE d WHERE d.DO_Domaine = l.DO_Domaine AND d.DO_Type = l.DO_Type AND d.DO_Piece = l.DO_Piece AND d.DO_Domaine IN (0, 1, 2) AND d.DO_Type NOT IN (8, 18, 22, 24, 25, 26, 27) AND (d.DO_Date >= '20260101' OR d.DO_Type IN (0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15) OR EXISTS (SELECT 1 FROM dbo.F_DOCREGL r WHERE r.DO_Domaine = d.DO_Domaine AND r.DO_Type = d.DO_Type AND r.DO_Piece = d.DO_Piece AND r.DR_Regle = 0))) ORDER BY l.DO_Domaine, l.DO_Type, l.DO_Piece, l.DL_Ligne;

-- echeances.csv  (F_DOCREGL)
SELECT x.DR_No, x.DO_Domaine, x.DO_Type, x.DO_Piece, x.DR_Date, x.DR_Montant, x.DR_Regle FROM dbo.F_DOCREGL AS x WHERE EXISTS (SELECT 1 FROM dbo.F_DOCENTETE d WHERE d.DO_Domaine = x.DO_Domaine AND d.DO_Type = x.DO_Type AND d.DO_Piece = x.DO_Piece AND d.DO_Domaine IN (0, 1, 2) AND d.DO_Type NOT IN (8, 18, 22, 24, 25, 26, 27) AND (d.DO_Date >= '20260101' OR d.DO_Type IN (0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15) OR EXISTS (SELECT 1 FROM dbo.F_DOCREGL r WHERE r.DO_Domaine = d.DO_Domaine AND r.DO_Type = d.DO_Type AND r.DO_Piece = d.DO_Piece AND r.DR_Regle = 0))) ORDER BY x.DR_No;

-- reglements.csv  (F_CREGLEMENT)
SELECT g.RG_No, g.CT_NumPayeur, g.RG_Date, g.RG_Montant, g.RG_Impute, g.RG_Libelle, g.RG_Reference, g.JO_Num FROM dbo.F_CREGLEMENT AS g WHERE g.RG_Montant > (SELECT ISNULL(SUM(c.RC_Montant), 0) FROM dbo.F_REGLECH AS c WHERE c.RG_No = g.RG_No) ORDER BY g.RG_No;

-- imputations.csv  (F_REGLECH)
SELECT c.RG_No, c.DR_No, c.RC_Montant FROM dbo.F_REGLECH AS c WHERE EXISTS (SELECT 1 FROM dbo.F_DOCREGL AS x WHERE x.DR_No = c.DR_No AND EXISTS (SELECT 1 FROM dbo.F_DOCENTETE d WHERE d.DO_Domaine = x.DO_Domaine AND d.DO_Type = x.DO_Type AND d.DO_Piece = x.DO_Piece AND d.DO_Domaine IN (0, 1, 2) AND d.DO_Type NOT IN (8, 18, 22, 24, 25, 26, 27) AND (d.DO_Date >= '20260101' OR d.DO_Type IN (0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15) OR EXISTS (SELECT 1 FROM dbo.F_DOCREGL r WHERE r.DO_Domaine = d.DO_Domaine AND r.DO_Type = d.DO_Type AND r.DO_Piece = d.DO_Piece AND r.DR_Regle = 0)))) ORDER BY c.RG_No, c.DR_No;
