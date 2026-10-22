/* =====================================================================================
   EXPORT SAGE 100 SQL SERVER → ERP OHADA — LECTURE SEULE
   -------------------------------------------------------------------------------------
   - Ces requêtes ne font que des SELECT : aucune donnée Sage n'est modifiée.
   - Exécutez-les d'abord sur une COPIE de test du dossier, avec un compte SQL en lecture seule.
   - Enregistrez chaque résultat dans le fichier CSV indiqué (SSMS : clic droit sur la grille
     › « Enregistrer les résultats sous… » ; gardez la ligne d'en-tête), dans un même dossier.
   - Toutes les colonnes figurent au catalogue V12.20 (skills SQL étapes 3 et 4). Sur une version plus
     ancienne, si SQL Server signale une colonne inconnue, retirez-la (les colonnes facultatives peuvent manquer).
   - Contrôle : la balance Sage éditée à la date de bascule doit donner les mêmes totaux que soldes.csv.
   ===================================================================================== */

DECLARE @DebutExercice date = '2026-01-01';   -- premier jour de l'exercice en cours dans Sage
DECLARE @DateBascule   date = '2026-12-31';   -- dernier jour repris (veille du démarrage dans l'ERP)

-- depots.csv
SELECT DE_No, DE_Intitule, DE_Principal, DE_Ville
FROM dbo.F_DEPOT
ORDER BY DE_No;

-- familles.csv (FA_Type = 0 : familles de détail ; les autres types sont ignorés à l'import)
SELECT FA_CodeFamille, FA_Intitule, FA_Type
FROM dbo.F_FAMILLE
ORDER BY FA_CodeFamille;

-- comptes.csv
SELECT CG_Num, CG_Intitule
FROM dbo.F_COMPTEG
ORDER BY CG_Num;

-- tiers.csv (CT_Type : 0 = client, 1 = fournisseur, 2 = salarié, 3 = autre ; seuls 0 et 1 sont repris)
SELECT CT_Num, CT_Intitule, CT_Type, CG_NumPrinc, CT_Ville, CT_Telephone, CT_EMail, CT_Sommeil, CT_NumPayeur
FROM dbo.F_COMPTET
ORDER BY CT_Num;

-- articles.csv (AR_PrixAch n'est pas le CMUP : la valeur du stock vient de stocks.csv)
SELECT AR_Ref, AR_Design, FA_CodeFamille, AR_SuiviStock, AR_Sommeil, AR_PrixAch, AR_PrixVen
FROM dbo.F_ARTICLE
ORDER BY AR_Ref;

-- stocks.csv : quantité EN STOCK (ni réservée, ni commandée, ni préparée) et valeur, par article et dépôt.
-- Articles à gammes ou suivis par lot : le détail F_GAMSTOCK / F_LOTSERIE n'est pas repris.
SELECT AR_Ref, DE_No, AS_QteSto, AS_MontSto, AS_QteMini, AS_QteMaxi
FROM dbo.F_ARTSTOCK
ORDER BY AR_Ref, DE_No;

-- soldes.csv : écritures de l'exercice en cours, à-nouveaux compris, jusqu'à la date de bascule.
-- Ne pas partir de la première année du dossier : les exercices clôturés sont déjà repris en à-nouveaux.
--  * Date comptable = période JM_Date + jour EC_Jour ; EC_Date est la date de SAISIE, pas celle de l'écriture.
--  * Norme nationale : EC_Norme 0 (les deux normes) ou 1 (nationale) ; 2 = IFRS seule, à ne pas additionner.
--  * Journaux de situation (JO_Type = 4) exclus : ce ne sont pas des écritures réelles.
--  * Un journal absent de F_JOURNAUX n'exclut pas ses écritures (anomalie à signaler, pas à masquer).
-- Ces trois filtres sont déduits du manuel V12.20 : le contrôle de la balance ci-dessus les valide.
SELECT e.CG_Num,
       ISNULL(e.CT_Num, '') AS CT_Num,
       SUM(CASE WHEN e.EC_Sens = 0 THEN e.EC_Montant ELSE 0 END) AS Debit,
       SUM(CASE WHEN e.EC_Sens = 1 THEN e.EC_Montant ELSE 0 END) AS Credit
FROM dbo.F_ECRITUREC AS e
LEFT JOIN dbo.F_JOURNAUX AS j ON j.JO_Num = e.JO_Num
WHERE DATEADD(day, e.EC_Jour - 1, e.JM_Date) BETWEEN @DebutExercice AND @DateBascule
  AND e.EC_Norme IN (0, 1)
  AND (j.JO_Type IS NULL OR j.JO_Type <> 4)
GROUP BY e.CG_Num, ISNULL(e.CT_Num, '')
ORDER BY e.CG_Num, CT_Num;
