/* EXEMPLES UNIQUEMENT — À UTILISER SUR DOSSIER DE DÉMONSTRATION.
   À valider selon la base .GCM/.MAE et les colonnes présentes.
   Aucune requête ci-dessous n'effectue de modification.
*/

-- Typologie de documents : ne constitue PAS un calcul de chiffre d'affaires.
SELECT DO_Domaine, DO_Type, DO_Provenance, DO_Valide, COUNT_BIG(*) AS NbPieces
FROM dbo.F_DOCENTETE
GROUP BY DO_Domaine, DO_Type, DO_Provenance, DO_Valide
ORDER BY DO_Domaine, DO_Type, DO_Provenance, DO_Valide;

-- Contrôle d'intégrité documentaire (ne nécessite pas de regroupements financiers)
SELECT TOP (100) d.DO_Domaine, d.DO_Type, d.DO_Piece, d.DO_Date,
       l.DL_No, l.DL_Ligne, l.AR_Ref, l.DL_Qte, l.DL_MvtStock
FROM dbo.F_DOCENTETE AS d
INNER JOIN dbo.F_DOCLIGNE AS l
 ON l.DO_Type=d.DO_Type AND l.DO_Piece=d.DO_Piece
WHERE d.DO_Domaine = 0
ORDER BY d.DO_Date DESC, d.DO_Type, d.DO_Piece, l.DL_Ligne;

-- Journal : lecture seule, somme débits / crédits à titre de contrôle;
-- filtrer exercice et journal et vérifier l'équilibre et le périmètre.
SELECT e.JO_Num, e.JM_Date,
       SUM(CASE WHEN e.EC_Sens=0 THEN e.EC_Montant ELSE 0 END) AS Debit,
       SUM(CASE WHEN e.EC_Sens=1 THEN e.EC_Montant ELSE 0 END) AS Credit
FROM dbo.F_ECRITUREC AS e
GROUP BY e.JO_Num, e.JM_Date
ORDER BY e.JM_Date, e.JO_Num;

-- Aucun CA/encours/stock théorique n'est calculé automatiquement :
-- construire et réconcilier ces contrats métier avant publication ERP.
