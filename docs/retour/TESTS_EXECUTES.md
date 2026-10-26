# Tests exécutés

Date : 2026-10-26 00:49 UTC. Commit de départ : voir `git log` (branche ccr-5592a371-fusjt2).
Environnement : Linux, Python 3.13, Django 6.1.2, SQLite (bases de test créées puis détruites).

## Suite complète du projet

```
python manage.py test -v 2
Ran 268 tests in 108.964s
OK
```

Détail par classe (les tests dont la description tient sur deux lignes ne sont pas comptés ici ; le total exact est la ligne « Ran » ci-dessus) :

| Module de test | Classe | Tests |
|---|---|---:|
| `apps.commercial.tests` | DocumentsVentesAchatsTests | 17 |
| `apps.commercial.tests` | StocksTests | 8 |
| `apps.commercial.tests_conformite_sage` | SensDesMouvementsTests | 1 |
| `apps.commercial.tests_fiche_stock` | FicheStockTests | 5 |
| `apps.commercial.tests_gros_detail` | GrosDetailTests | 6 |
| `apps.commercial.tests_payeur` | DoublonTiersTests | 1 |
| `apps.commercial.tests_payeur` | TiersPayeurTests | 6 |
| `apps.commercial.tests_recette` | AteliersTests | 2 |
| `apps.commercial.tests_recette` | CasPratiquesTests | 13 |
| `apps.commercial.tests_recette` | EcransEtatsV12Tests | 2 |
| `apps.commercial.tests_tva` | FiscaliteCamerounTests | 3 |
| `apps.commercial.tests_tva` | RegimeTvaTests | 9 |
| `apps.comptabilite.tests` | ComptabiliteTests | 7 |
| `apps.comptabilite.tests_liaison` | LiaisonComptableTests | 9 |
| `apps.comptabilite.tests_recette` | CloturesTests | 4 |
| `apps.comptabilite.tests_recette` | EcransComptaTests | 2 |
| `apps.comptabilite.tests_recette` | EtatsTiersTests | 2 |
| `apps.comptabilite.tests_recette` | InterModulesTests | 4 |
| `apps.comptabilite.tests_recette` | LettrageTests | 2 |
| `apps.comptabilite.tests_recette` | RapprochementTests | 1 |
| `apps.comptabilite.tests_recette` | StructureTests | 2 |
| `apps.core.tests_accueil` | PageAccueilTests | 1 |
| `apps.core.tests_autorisations` | AutorisationsTests | 8 |
| `apps.core.tests_fichiers_lies` | FichiersLiesTests | 3 |
| `apps.core.tests_journal` | JournalEvenementsTests | 5 |
| `apps.core.tests_reprise_sage` | RepriseSageTests | 10 |
| `apps.core.tests_reprise_sage_complete` | EcranRepriseTests | 3 |
| `apps.core.tests_reprise_sage_complete` | InstancesSqlTests | 3 |
| `apps.core.tests_reprise_sage_complete` | RepriseCompleteTests | 6 |
| `apps.core.tests_reprise_sage_complete` | RequetesSageTests | 3 |
| `apps.core.tests_revue_gpt` | ReportReview | 2 |
| `apps.core.tests_revue_gpt` | StockReview | 8 |
| `apps.core.tests_sauvegarde` | SauvegardeTests | 3 |
| `apps.core.tests_selection` | FenetreSelectionTests | 5 |
| `apps.echanges.tests` | EcranEchangesTests | 1 |
| `apps.echanges.tests` | LotsTests | 2 |
| `apps.echanges.tests` | ScenarioTroisDossiersTests | 1 |
| `apps.garage.tests` | GarageTests | 2 |
| `apps.partenaires.tests` | PartenairesTests | 7 |
| `apps.partenaires.tests` | RemunerationsProprietairesTests | 5 |
| `apps.personnel.tests` | PaieTests | 1 |
| `apps.reporting.tests` | PagesEtApiTests | 8 |
| `apps.reporting.tests_rapport_commercial` | RapportCommercialTests | 9 |
| `apps.transport.tests` | AnomaliesRapportJournalierTests | 3 |
| `apps.transport.tests` | BagagesTests | 3 |
| `apps.transport.tests` | BilletterieAvanceeTests | 6 |
| `apps.transport.tests` | CaissesEtCloturesTests | 2 |
| `apps.transport.tests` | ComparaisonsTransportTests | 2 |
| `apps.transport.tests` | ComptabiliteAnalytiqueTests | 5 |
| `apps.transport.tests` | ComptesVehiculesTests | 1 |
| `apps.transport.tests` | CorrespondanceTests | 3 |
| `apps.transport.tests` | DepensesFonctionnementTests | 3 |
| `apps.transport.tests` | EcransTransportTests | 3 |
| `apps.transport.tests` | ExploitationTests | 2 |
| `apps.transport.tests` | ImprevusTests | 5 |
| `apps.transport.tests` | JourneeAgenceTests | 1 |
| `apps.transport.tests` | NumerotationAgencesTests | 2 |
| `apps.transport.tests` | RapportJournalierA4Tests | 2 |
| `apps.transport.tests` | SystemeMinimalTresorerieTests | 2 |
| `apps.transport.tests` | TransportTests | 12 |

Le scénario `apps.echanges` crée **quatre bases séparées** (siège, Douala, Yaoundé, Bertoua) qui ne communiquent que par fichiers signés : billets, colis entre agences, correspondance, consolidation (liaisons à 0), rejeu sans effet, fichier altéré refusé, dépense payée pour une autre agence.

## Validateurs fournis par les skills (données CSV fictives, pas la base de l'ERP)

```
python3 -I .claude/skills/erp-transport-simulation-complete/scripts/validate_demo.py
VALIDATION OK: 8 agences, 300 salaries, 60 voyageurs dont 15 partenaires, 5 courriers.
OK: 1275 voyages, 35883 billets sieges uniques, 2523 colis, 32 BC, 300 paies, 12695 ecritures GA, 12607 allocations analytiques.
OK: Debit = Credit = 803,114,750 FCFA. Toutes allocations financieres sourcées GA. 30 jours x 8 agences.
ATTENTION: données et taux de paie fictifs, pas un paramétrage SYSCOHADA légal. Aucun test du vrai projet ERP n’est réalisé ici.

python3 -I .claude/skills/erp-transport-partenaires-proprietaires/scripts/validate_exemple.py
OK — écritures GA équilibrées, imputations toutes sourcées, résultat véhicule 270 000 FCFA, droits 330 000 FCFA, payé 250 000 FCFA, solde dû 80 000 FCFA, rôle fournisseur séparé.
```

## Ce qui n'a PAS été exécuté

- Import de la simulation « septembre 2026 » (8 agences, 300 salariés, 35 883 billets) dans une base de l'ERP : non fait (voir `BILAN_SIMULATION_SEPTEMBRE_2026.md`).
- Tests de charge, de concurrence réelle sur plusieurs postes, et sur PostgreSQL / SQL Server.
- Rendu imprimé : le rapport A4 a été contrôlé en PDF (navigateur Chromium) le 26/10 sur des données fictives.
