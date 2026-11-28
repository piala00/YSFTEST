---
name: erp-transport-comptabilite-source-unique
description: Appliquer à l'ERP Transport Afrique Centrale la règle non négociable selon laquelle toute écriture monétaire analytique provient d'une écriture préalable validée en comptabilité générale, avec traçabilité, ventilation équilibrée, contrôles d'intégrité, rapprochements, correction par contrepassation et prise en charge offline-first. Préserver les deux familles d'états analytiques Véhicules et Propriétaires et le reporting comparatif transversal.
---

# Claude Code — Comptabilité générale : source UNIQUE des écritures analytiques

## Décision du maître d'ouvrage — priorité maximale

> **AUCUNE ÉCRITURE MONÉTAIRE EN COMPTABILITÉ ANALYTIQUE SANS ÉCRITURE SOURCE PRÉALABLEMENT VALIDÉE EN COMPTABILITÉ GÉNÉRALE.**

Cette instruction prévaut sur toute ancienne consigne laissant entendre qu'une recette, dépense, charge ou créance pourrait être **créée directement** par le moteur analytique sur la seule base d'une opération de billetterie, d'un ticket de caisse, d'une fiche garage, d'une feuille de route ou d'un contrat partenaire.

- La **comptabilité générale** est le grand livre et la seule vérité monétaire comptable de la société : écritures SYSCOHADA, journaux, comptes, tiers, justificatifs, contrôle des soldes et périodes.
- La **comptabilité analytique** est un **détail / une ventilation / une restitution** des montants des écritures générales éligibles ; pas une deuxième comptabilité, pas un autre journal financier indépendant.
- Le moteur analytique **ne crée ni recette ni charge, ni dette ni créance** absente de la générale. Une ventilation peut décomposer un montant existant sur plusieurs véhicules, avec somme algébrique identique.
- Une ligne monétaire analytique **doit conserver `source_gl_entry_id` et idéalement `source_gl_line_id`** (ou clé technique équivalente) permettant drill-down vers pièce, journal, compte, tiers, auteur et statut.
- **Seules les écritures GÉNÉRALES VALIDÉES / COMPTABILISÉES** alimentent les états analytiques financiers définitifs. Les faits opérationnels avant comptabilisation restent dans le suivi des opérations / anomalies, explicitement « non comptabilisé » ou « provisoire », jamais discrètement intégrés aux montants définitifs.
- Tout avoir, annulation ou correction comptable utilise une écriture corrective/contrepassation selon règles validées ; la ventilation analytique est recalculée / inversée de manière traçable. Ne jamais effacer silencieusement une source utilisée.
- Tout total analytique doit être **rapprochable** avec le sous-ensemble défini d'écritures du grand livre, avec traitement explicite de « non ventilé », de l'arrondi et des montants non éligibles.

## Chaîne comptable obligatoire

`Service métier → fait opérationnel et justificatif → règle comptable → écriture équilibrée en comptabilité générale → validation/posting → ligne(s) analytiques dérivées et traçables → états Véhicules/Propriétaires → Reporting décisionnel`

Aucun chemin de contournement. La saisie analytique manuelle, si une interface d'affectation est prévue, n'autorise que la **modification contrôlée des dimensions/ventilations d'écritures générales déjà validées** ; elle ne permet jamais de créer un montant sans source GL.

## Frontières de l'architecture existante (NE PAS modifier arbitrairement)

```text
GESTION COMPTABLE
  1. Comptabilité générale
     Plan comptable, journaux, tiers, pièces, écritures, soldes, états SYSCOHADA
     Plans analytiques et règles d'affectation partagés
  2. Comptabilité analytique
     A. Véhicules — recettes, charges, voyages, résultat, traçabilité
     B. Propriétaires — exploitation des véhicules, droits contractuels,
        avances/règlements comptabilisés, solde comptable auxiliaire

REPORTING / ANALYSES DÉCISIONNELLES (module distinct)
  Comparaisons agences, véhicules, périodes, lignes, Classique/VIP,
  avec les mêmes montants analytiques réconciliés et KPI opérationnels distincts
```

Plans/agences, partenaires, lignes, voyages, services, gammes VIP/Classique, contrats et canaux sont des **axes/sections/attributs** ; pas des comptabilités indépendantes ni des onglets principaux supplémentaires dans Comptabilité analytique.

## Règles métier à respecter

1. Flottes **Classique** et **VIP** distinctes, affectation datée ; historique du propriétaire/contrat daté.
2. Distinguer agence de vente, agence d'exploitation, lieu de départ et caisse ; ne jamais assimiler automatiquement encaissement à produit de l'exercice ou du voyage.
3. Une caisse peut être unique dans une petite agence ou multiple au siège / dans les grandes agences. Les virements entre caisses sont des mouvements de trésorerie, pas des recettes commerciales nouvelles.
4. Les charges de garage (notamment pièces) sont imputées au véhicule selon la **consommation comptabilisée**, pas nécessairement au simple achat du stock ; une immobilisation n'est pas arbitrairement traitée comme une charge.
5. Salaires/charges d'équipages : utiliser les montants de paie comptabilisés ; répartir ensuite selon règles validées, sans enregistrer une seconde charge.
6. Propriétaire : séparer **résultat d'exploitation du véhicule**, **droits théoriques calculés suivant contrat**, **sommes dues comptabilisées au compte du partenaire**, **paiements comptabilisés**. Un droit calculé n'est pas automatiquement un solde comptable définitif tant que les écritures requises ne sont pas passées en générale.
7. Les kilomètres, voyages, passagers, sièges et colis sont **données non monétaires** issues de l'exploitation. Ils complètent les états mais ne constituent pas des écritures analytiques ; toute recette/charge affichée provient de la générale.
8. Hors connexion : une agence peut comptabiliser localement si elle possède la compétence et les contrôles prévus ; état « validé localement / synchronisation en attente » au siège. Les montants globaux restent provisoires si des agences ne sont pas synchronisées ; identifiants de posting idempotents.

## Étapes d'exécution obligatoires pour Claude Code

1. AUDITER d'abord les véritables modèles de données, tables, écrans, APIs, règles de billetterie/courrier/garage/paie, écritures, postes et synchronisations ; ne pas inventer des tables déjà existantes.
2. Identifier toutes les sources de montants actuelles en analytique et reporting ; lister les chemins qui contournent le grand livre. Proposer un plan de remédiation avec diagnostic des lignes historiques sans source.
3. Créer/adapter les contraintes de référence analytique→ligne GL validée, les règles de publication, la gestion des allocations, les statuts, les contrôles et la journalisation. Réutiliser le schéma existant dès que possible.
4. Effectuer des **migrations additives, transactionnelles et sauvegardées** ; aucune suppression automatique de données historiques. Mettre les enregistrements orphelins dans une file d'anomalies jusqu'à rapprochement, sans leur inventer une écriture source.
5. Adapter les états véhicules, partenaires et le reporting pour ne lire que des montants analytiques sourcés ; afficher lignes non ventilées, changements, dates de clôture et statut de synchronisation.
6. Écrire les tests unitaires, d'intégration, de contrôle d'accès, de réconciliation comptable, de contrepassation, de multi-agences offline et de non-régression.
7. Livrer un compte rendu exact : fichiers modifiés, migrations, tests réellement exécutés, anomalies historiques, règles comptables nécessitant validation d'un expert SYSCOHADA.

## Références du Skill

- [01 — Contrat comptable et états](references/01-invariants-source-unique.md)
- [02 — Parcours des services vers le grand livre](references/02-workflows-services.md)
- [03 — Schéma relationnel et événements](references/03-modele-sql-et-evenements.md)
- [04 — Rapprochements et contrôles](references/04-reconciliation-et-integrite.md)
- [05 — États véhicules, propriétaires et reporting](references/05-etats-et-proprietaires.md)
- [06 — Synchronisation et clôture](references/06-offline-clotures.md)
- [07 — Cas de test et méthode de mise à jour](references/07-tests-et-deploiement.md)
- [08 — Cas chiffré de ventilation](references/08-exemple-de-bout-en-bout.md)

Ce Skill complète `/erp-transport-afrique-centrale`, `/erp-transport-plan-analytique`, `/erp-transport-comptabilite-generale-analytique` et `/erp-transport-reporting-analytique`. **En cas de divergence, cette règle “générale d'abord” est prioritaire pour tout montant comptable.**

## Instruction prête à soumettre à Claude Code

> Applique `/erp-transport-comptabilite-source-unique` dans mon ERP Transport. Avant toute modification, audite le code, les tables SQL, la génération des écritures, les calculs analytiques et le reporting. Impose qu'aucune ligne analytique financière ne puisse exister sans ligne comptable générale préalablement validée et traçable. Toute ventilation garde le montant total source et les écritures non ventilées restent visibles en anomalie. Comptabilité analytique = uniquement états Véhicules et Propriétaires ; Reporting = comparaisons agences/véhicules/périodes sur les mêmes écritures. Préserve toutes les données, adapte l'offline et la synchronisation, crée migrations sûres et tests, puis rends compte des modifications vraiment réalisées.
