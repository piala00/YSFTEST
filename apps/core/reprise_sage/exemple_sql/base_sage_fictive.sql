/* Base Sage 100 FICTIVE pour tester la reprise en lecture directe (données inventées, aucune donnée réelle).
   Ne contient que les tables et colonnes lues par la reprise de l'ERP ; à créer dans une base de TEST vide,
   jamais dans un dossier Sage. Exercice 2026, bascule au 31/10/2026. */

CREATE TABLE P_DOSSIER (D_RaisonSoc varchar(69));
INSERT INTO P_DOSSIER VALUES ('Société Fictive SARL');

CREATE TABLE F_DEPOT (DE_No int, DE_Intitule varchar(35), DE_Principal smallint, DE_Ville varchar(35));
CREATE TABLE F_FAMILLE (FA_CodeFamille varchar(10), FA_Intitule varchar(69), FA_Type smallint);
CREATE TABLE F_COMPTEG (CG_Num varchar(13), CG_Intitule varchar(35), CG_Type smallint);
CREATE TABLE F_JOURNAUX (JO_Num varchar(6), JO_Intitule varchar(35), JO_Type smallint, CG_Num varchar(13));
CREATE TABLE F_COMPTEA (N_Analytique smallint, CA_Num varchar(13), CA_Intitule varchar(35), CA_Type smallint, CA_Sommeil smallint);
CREATE TABLE F_TAXE (TA_Code varchar(5), TA_Intitule varchar(35), TA_Taux numeric(24,6), TA_Sens smallint, CG_Num varchar(13));
CREATE TABLE F_COMPTET (CT_Num varchar(17), CT_Intitule varchar(69), CT_Type smallint, CG_NumPrinc varchar(13), CT_Ville varchar(35),
  CT_Telephone varchar(21), CT_EMail varchar(69), CT_Sommeil smallint, CT_NumPayeur varchar(17), N_CatTarif smallint, CT_Encours numeric(24,6));
CREATE TABLE F_ARTICLE (AR_Ref varchar(19), AR_Design varchar(69), FA_CodeFamille varchar(10), AR_SuiviStock smallint, AR_Sommeil smallint,
  AR_PrixAch numeric(24,6), AR_PrixVen numeric(24,6));
CREATE TABLE F_ARTCLIENT (AR_Ref varchar(19), AC_Categorie smallint, CT_Num varchar(17), AC_PrixVen numeric(24,6));
CREATE TABLE F_ARTSTOCK (AR_Ref varchar(19), DE_No int, AS_QteSto numeric(24,6), AS_MontSto numeric(24,6), AS_QteMini numeric(24,6), AS_QteMaxi numeric(24,6));
CREATE TABLE F_ECRITUREC (EC_No int, JO_Num varchar(6), JM_Date datetime, EC_Jour smallint, EC_Piece varchar(13), CG_Num varchar(13),
  CT_Num varchar(17), EC_Sens smallint, EC_Montant numeric(24,6), EC_Intitule varchar(69), EC_Lettrage varchar(3), EC_Norme smallint);
CREATE TABLE F_ECRITUREA (EC_No int, N_Analytique smallint, CA_Num varchar(13), EA_Montant numeric(24,6));
CREATE TABLE F_DOCENTETE (DO_Domaine smallint, DO_Type smallint, DO_Piece varchar(13), DO_Date datetime, DO_Tiers varchar(17), DO_Ref varchar(17),
  DE_No int, DO_Provenance smallint, CT_NumPayeur varchar(17));
CREATE TABLE F_DOCLIGNE (DO_Domaine smallint, DO_Type smallint, DO_Piece varchar(13), DL_No int, DL_Ligne int, AR_Ref varchar(19), DL_Design varchar(69),
  DL_Qte numeric(24,6), DL_MontantHT numeric(24,6), DL_MontantTTC numeric(24,6));
CREATE TABLE F_DOCREGL (DR_No int, DO_Domaine smallint, DO_Type smallint, DO_Piece varchar(13), DR_Date datetime, DR_Montant numeric(24,6), DR_Regle smallint);
CREATE TABLE F_CREGLEMENT (RG_No int, CT_NumPayeur varchar(17), RG_Date datetime, RG_Montant numeric(24,6), RG_Impute smallint,
  RG_Libelle varchar(35), RG_Reference varchar(17), JO_Num varchar(6));
CREATE TABLE F_REGLECH (RG_No int, DR_No int, RC_Montant numeric(24,6));

INSERT INTO F_DEPOT VALUES (1, 'Magasin principal', 1, 'Ville A'), (2, 'Boutique', 0, 'Ville A');
INSERT INTO F_FAMILLE VALUES ('ALIM', 'Alimentation', 0), ('TOTAL', 'Total familles', 2);
INSERT INTO F_COMPTEG VALUES ('101000', 'Capital', 0), ('401100', 'Fournisseurs', 0), ('411100', 'Clients', 0), ('41', 'Total tiers', 1),
  ('421000', 'Personnel avances', 0), ('443100', 'TVA collectée', 0), ('445200', 'TVA déductible', 0), ('521100', 'Banque A', 0),
  ('571100', 'Caisse', 0), ('601100', 'Achats marchandises', 0), ('701100', 'Ventes marchandises', 0);
INSERT INTO F_JOURNAUX VALUES ('VTE', 'Ventes', 1, NULL), ('ACH', 'Achats', 0, NULL), ('BQ1', 'Banque A', 2, '521100'),
  ('CAI', 'Caisse', 2, '571100'), ('RAN', 'Reports à nouveau', 3, NULL), ('SIT', 'Situation', 4, NULL);
INSERT INTO F_COMPTEA VALUES (1, 'AG01', 'Agence Est', 0, 0), (1, 'AG02', 'Agence Nord', 0, 0), (1, 'TOT', 'Total agences', 1, 0),
  (2, 'AG01', 'Activité huile', 0, 0);
INSERT INTO F_TAXE VALUES ('T19', 'TVA collectée 19,25', 19.25, 1, '443100'), ('D19', 'TVA déductible 19,25', 19.25, 0, '445200');
INSERT INTO F_COMPTET VALUES ('CL001', 'Client Un', 0, '411100', 'Ville A', '600000001', 'un@exemple.test', 0, 'CL001', 1, 500000),
  ('CL002', 'Client Deux', 0, '411100', 'Ville B', '', '', 0, 'CL002', 0, 0),
  ('FR001', 'Fournisseur Un', 1, '401100', 'Ville C', '', '', 0, 'FR001', 0, 0),
  ('SA001', 'Salarié Un', 2, '421000', '', '', '', 0, 'SA001', 0, 0);
INSERT INTO F_ARTICLE VALUES ('HUI15', 'Huile carton 15 L', 'ALIM', 2, 0, 9000, 11500), ('RIZ50', 'Riz sac 50 kg', 'ALIM', 2, 0, 15000, 25000);
INSERT INTO F_ARTCLIENT VALUES ('HUI15', 1, '', 11000), ('HUI15', 0, 'CL002', 10500);
INSERT INTO F_ARTSTOCK VALUES ('HUI15', 1, 40, 360000, 5, 100), ('RIZ50', 1, 20, 300000, 0, 0), ('HUI15', 2, 5, 45000, 0, 0);

-- Écritures 2026 (JM_Date = 1er jour de la période, EC_Jour = jour)
INSERT INTO F_ECRITUREC VALUES
 (1, 'RAN', '2026-01-01', 1, 'AN1', '521100', NULL, 0, 1000000, 'Report banque', '', 0),
 (2, 'RAN', '2026-01-01', 1, 'AN1', '571100', NULL, 0, 200000, 'Report caisse', '', 0),
 (3, 'RAN', '2026-01-01', 1, 'AN1', '101000', NULL, 1, 1200000, 'Report capital', '', 0),
 (4, 'VTE', '2026-09-01', 10, 'FA001', '411100', 'CL001', 0, 238500, 'Facture FA001', 'A', 0),
 (5, 'VTE', '2026-09-01', 10, 'FA001', '701100', NULL, 1, 200000, 'Facture FA001', '', 0),
 (6, 'VTE', '2026-09-01', 10, 'FA001', '443100', NULL, 1, 38500, 'Facture FA001', '', 0),
 (7, 'VTE', '2026-10-01', 5, 'FA002', '411100', 'CL001', 0, 119250, 'Facture FA002', '', 0),
 (8, 'VTE', '2026-10-01', 5, 'FA002', '701100', NULL, 1, 100000, 'Facture FA002', '', 0),
 (9, 'VTE', '2026-10-01', 5, 'FA002', '443100', NULL, 1, 19250, 'Facture FA002', '', 0),
 (10, 'VTE', '2026-10-01', 20, 'FA003', '411100', 'CL002', 0, 59625, 'Facture FA003', '', 0),
 (11, 'VTE', '2026-10-01', 20, 'FA003', '701100', NULL, 1, 50000, 'Facture FA003', '', 0),
 (12, 'VTE', '2026-10-01', 20, 'FA003', '443100', NULL, 1, 9625, 'Facture FA003', '', 0),
 (13, 'VTE', '2026-10-01', 25, 'AV001', '411100', 'CL002', 1, 11925, 'Avoir AV001', '', 0),
 (14, 'VTE', '2026-10-01', 25, 'AV001', '701100', NULL, 0, 10000, 'Avoir AV001', '', 0),
 (15, 'VTE', '2026-10-01', 25, 'AV001', '443100', NULL, 0, 1925, 'Avoir AV001', '', 0),
 (16, 'ACH', '2026-10-01', 2, 'FF001', '601100', NULL, 0, 300000, 'Facture FF001', '', 0),
 (17, 'ACH', '2026-10-01', 2, 'FF001', '445200', NULL, 0, 57750, 'Facture FF001', '', 0),
 (18, 'ACH', '2026-10-01', 2, 'FF001', '401100', 'FR001', 1, 357750, 'Facture FF001', '', 0),
 (19, 'BQ1', '2026-09-01', 20, 'RG1', '521100', NULL, 0, 238500, 'Règlement CL001', '', 0),
 (20, 'BQ1', '2026-09-01', 20, 'RG1', '411100', 'CL001', 1, 238500, 'Règlement CL001', 'A', 0),
 (21, 'CAI', '2026-10-01', 15, 'RG2', '571100', NULL, 0, 50000, 'Acompte CL001', '', 0),
 (22, 'CAI', '2026-10-01', 15, 'RG2', '411100', 'CL001', 1, 50000, 'Acompte CL001', '', 0),
 (23, 'CAI', '2026-10-01', 28, 'RG3', '571100', NULL, 0, 30000, 'Versement CL002', '', 0),
 (24, 'CAI', '2026-10-01', 28, 'RG3', '411100', 'CL002', 1, 30000, 'Versement CL002', '', 0),
 (25, 'CAI', '2026-10-01', 29, 'AV1', '421000', 'SA001', 0, 20000, 'Avance salarié', '', 0),
 (26, 'CAI', '2026-10-01', 29, 'AV1', '571100', NULL, 1, 20000, 'Avance salarié', '', 0),
 (27, 'SIT', '2026-10-01', 31, 'SIT1', '601100', NULL, 0, 999, 'Situation (exclue)', '', 0),
 (28, 'SIT', '2026-10-01', 31, 'SIT1', '401100', NULL, 1, 999, 'Situation (exclue)', '', 0),
 (29, 'RAN', '2026-01-01', 1, 'IF1', '601100', NULL, 0, 5, 'IFRS seule (exclue)', '', 2),
 (30, 'RAN', '2026-01-01', 1, 'IF1', '101000', NULL, 1, 5, 'IFRS seule (exclue)', '', 2),
 (31, 'VTE', '2026-11-01', 3, 'FA009', '411100', 'CL001', 0, 1000, 'Après la bascule (exclue)', '', 0),
 (32, 'VTE', '2026-11-01', 3, 'FA009', '701100', NULL, 1, 1000, 'Après la bascule (exclue)', '', 0);
INSERT INTO F_ECRITUREA VALUES (5, 1, 'AG01', 150000), (5, 1, 'AG02', 50000), (5, 2, 'AG01', 200000), (8, 1, 'AG01', 100000);

-- Pièces commerciales
INSERT INTO F_DOCENTETE VALUES
 (0, 7, 'FA001', '2026-09-10', 'CL001', 'CDE-1', 1, 0, 'CL001'),
 (0, 7, 'FA002', '2026-10-05', 'CL001', '', 1, 0, 'CL001'),
 (0, 7, 'FA003', '2026-10-20', 'CL002', '', 1, 0, 'CL002'),
 (0, 7, 'AV001', '2026-10-25', 'CL002', '', 1, 2, 'CL002'),
 (0, 1, 'BC0001', '2026-10-29', 'CL001', '', 1, 0, 'CL001'),
 (0, 3, 'BL0001', '2026-10-30', 'CL002', '', 1, 0, 'CL002'),
 (0, 0, 'DE0001', '2025-06-01', 'CL001', '', 1, 0, 'CL001'),
 (0, 7, 'FA000', '2025-12-15', 'CL001', '', 1, 0, 'CL001'),
 (0, 8, 'AR0001', '2026-03-01', 'CL001', '', 1, 0, 'CL001'),
 (1, 17, 'FF001', '2026-10-02', 'FR001', 'BL-F1', 1, 0, 'FR001'),
 (2, 20, 'ME0001', '2026-01-02', '1', '', 1, 0, NULL),
 (2, 23, 'MT0001', '2026-02-02', '2', '', 1, 0, NULL);
INSERT INTO F_DOCLIGNE VALUES
 (0, 7, 'FA001', 1, 1, 'HUI15', 'Huile carton 15 L', 2, 200000, 238500),
 (0, 7, 'FA002', 2, 1, 'HUI15', 'Huile carton 15 L', 1, 100000, 119250),
 (0, 7, 'FA003', 3, 1, 'RIZ50', 'Riz sac 50 kg', 1, 50000, 59625),
 (0, 7, 'FA003', 4, 2, NULL, 'Livraison le 20/10', 0, 0, 0),
 (0, 7, 'AV001', 5, 1, NULL, 'Remise commerciale', 1, 10000, 11925),
 (0, 1, 'BC0001', 6, 1, 'HUI15', 'Huile carton 15 L', 3, 300000, 357750),
 (0, 3, 'BL0001', 7, 1, 'RIZ50', 'Riz sac 50 kg', 2, 100000, 119250),
 (0, 0, 'DE0001', 8, 1, 'RIZ50', 'Riz sac 50 kg', 10, 250000, 298125),
 (0, 7, 'FA000', 9, 1, 'RIZ50', 'Riz sac 50 kg', 1, 25000, 29813),
 (1, 17, 'FF001', 10, 1, 'RIZ50', 'Riz sac 50 kg', 20, 300000, 357750),
 (2, 20, 'ME0001', 11, 1, 'HUI15', 'Huile carton 15 L', 40, 360000, 360000),
 (2, 23, 'MT0001', 12, 1, 'HUI15', 'Huile carton 15 L', 5, 45000, 45000);
INSERT INTO F_DOCREGL VALUES
 (1, 0, 7, 'FA001', '2026-10-10', 238500, 1),
 (2, 0, 7, 'FA002', '2026-11-04', 119250, 0),
 (3, 0, 7, 'FA003', '2026-11-19', 59625, 0),
 (4, 1, 17, 'FF001', '2026-11-01', 357750, 0),
 (5, 0, 7, 'FA000', '2026-01-14', 29813, 1);
INSERT INTO F_CREGLEMENT VALUES
 (1, 'CL001', '2026-09-20', 238500, 1, 'Règlement FA001', 'VIR-1', 'BQ1'),
 (2, 'CL001', '2026-10-15', 50000, 1, 'Acompte FA002', '', 'CAI'),
 (3, 'CL002', '2026-10-28', 30000, 0, 'Versement CL002', 'REC-3', 'CAI');
INSERT INTO F_REGLECH VALUES (1, 1, 238500), (2, 2, 50000);
