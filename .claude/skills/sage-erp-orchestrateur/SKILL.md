---
name: sage-erp-orchestrateur
description: "Orchestrer les compétences Sage 100 V5-V12, Objets Métiers, BI et Sage X3 pour développer un ERP fiable, avec collecte probante et contrats de synchronisation."
---

# Gouvernance globale Sage → ERP

## Mission
Aider à développer l'ERP en utilisant les produits Sage comme **sources de vérité fonctionnelle**, sans confondre produits, versions ou niveaux de preuve. Lire aussi les Skills spécialisés selon les demandes. **Ne jamais prétendre disposer de tous les écrans/champs si la matrice de couverture ne le prouve pas.**

## Routage
- Sage 100 ventes/achats/stock → `sage100-gescom-v5-v12-expert`.
- Sage 100 écritures/comptes/banques/états → `sage100-comptabilite-v5-v12-expert`.
- Créer/modifier dans Sage depuis l'ERP → `sage100-objets-metiers-v5-v12`.
- Analyse Excel / cubes / BI / indicateurs → `sage-bi-reporting-expert`.
- Sage X3 → `sage-x3-v12-expert`.

## Architecture préférentielle ERP
1. Bases SQL Sage d'agence = systèmes sources, n'opérer que des lectures depuis les connexions reporting.
2. Service d'extraction versionné par produit/installation, droits SQL minimaux, watermark et réconciliation ; tout import ou modification dans Sage se fait avec interface autorisée, **pas par écriture directe SQL métier**.
3. Staging immuable (`source_system`, `source_database`, `company`, `agency`, `source_pk`, `source_updated_at`, `extracted_at`, `batch_id`, `hash`, `schema_version`).
4. Base analytique ERP indépendante : référentiels harmonisés et vues matérialisées/pipelines avec historique, contrôles et provenance.
5. Application bureau/web lit sa base ERP, non Sage directement, sauf commande d'écriture explicitement mise en œuvre et sécurisée.
6. Services métier dédiés pour retours, stocks, règlement/lettrage, périodes, taxes et multi-devises.

## Règles de sûreté
- Jamais d'`INSERT/UPDATE/DELETE/MERGE/EXEC` applicatif direct contre une base Sage en production. Ne pas affirmer que toutes les tables marquées 'écriture' dans le manuel sont librement modifiables avec SQL ; ces indications concernent des interfaces documentées.
- Avant toute intégration COM/SDK : compatibilité édition/version/build, 32/64 bits, licences, COM sur Windows, droits et essais copie.
- Extraction SQL sans modification = données secrètes protégées ; minimisation, chiffrement, rôles, audit.
- Sur anomalies : comparer à une sortie Sage de référence ; ne pas masquer un écart avec un filtre arbitraire.
- Pour les règles OHADA/SYSCOHADA, la comptabilisation locale dépend du plan, des versions et paramétrages : ne pas appliquer automatiquement la fiscalité France.

## Protocole de connaissance
Lire `resources/schemas/NOTICE.md`, `resources/sources/SOURCES_OFFICIELLES.md`, puis `resources/schemas/matrice_versions.csv`. Produire une fiche contrôlée pour chaque fonction ; statuts : REPÉRÉ, DOCUMENTÉ, OBSERVÉ, TESTÉ, VALIDÉ ; citer preuve et version exacte. Exiger validation laboratoire pour changements.

## Livrables attendus de Claude
Spécification fonctionnelle > navigation UI (menu, fenêtre, onglet, champ) > règles et permissions > mapping SQL/SDK > cas de test > preuves > différentiel versions > intégration ERP. Toujours distinguer **fonction constatée** et **fonction à vérifier**.

