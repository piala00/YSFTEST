---
name: erp-transport-reporting-analytique
description: Auditer, concevoir et développer le reporting décisionnel de l'ERP Transport Afrique Centrale à partir d'un référentiel analytique relié à la comptabilité générale et aux opérations métier. Produire comparaisons par dates, véhicules, propriétaires, agences, lignes et gammes Classique/VIP ; analyses de performance, indicateurs fiables, rapprochements OHADA, tableaux simples, exports, permissions et fonctionnement offline-first. Préserver la navigation Comptabilité générale / Comptabilité analytique (Véhicules et Propriétaires) ; Reporting est un module transversal distinct.
---

> **DÉCISION COMPTABLE PRIORITAIRE (25/10/2026) :** toute ligne analytique MONÉTAIRE doit obligatoirement dériver d'une ligne comptable GÉNÉRALE préalablement validée/postée, avec référence traçable. La comptabilité analytique ne peut créer des recettes, dépenses, dettes ni créances indépendantes. Voir `/erp-transport-comptabilite-source-unique` ; il prévaut sur les anciennes formulations contraires. Les KPI non monétaires restent issus de l'exploitation.


# Skill Claude Code — Reporting fondé sur la comptabilité analytique

## Décision métier validée — prioritaire

1. **La comptabilité générale est la référence réglementaire et financière** de chaque société (écritures, tiers, journaux, balances, états SYSCOHADA). Ne pas fabriquer une seconde comptabilité légale.
2. **La comptabilité analytique est un système de gestion détaillé relié à la générale**, capable de ventiler ses écritures éligibles et d'utiliser les informations métier complémentaires (voyages, sièges, kilomètres, colis, contrats). Une charge de gestion répartie n'est pas une nouvelle écriture du grand livre.
3. Dans **Gestion comptable**, conserver exactement **deux sous-modules visibles** : (i) Comptabilité générale et (ii) Comptabilité analytique, cette dernière ne possédant que **deux familles principales d'états : Véhicules et Propriétaires de véhicules**.
4. Le **Reporting / Analyses décisionnelles** utilise les plans, sections, ventilations et agrégats analytiques comme **moteur d'explication et de comparaison** ; il exploite aussi, si nécessaire, les données opérationnelles et les écritures comptables correspondantes. Le reporting n'est **pas** une troisième comptabilité et ne doit pas créer un sous-module analytique concurrent.
5. Les plans Agences, Services, Activités, Gammes Classique/VIP, Lignes, Voyages, Contrats, Canaux de vente, Véhicules et Propriétaires restent des **dimensions de données et de filtres**, sans multiplier les deux familles de restitution analytique.
6. **Classique et VIP sont des flottes distinctes**, pas des sièges mélangés dans un même véhicule pour un même intervalle d'affectation. Conserver l'historique des réaffectations datées et les contrats de propriétaire datés.
7. **Le rapport journalier d'agence reste un ensemble de tableaux très simples** (billetterie par départ/itinéraire, bagages, colis, sorties, caisse et remises). Les tableaux comparatifs, analyses et graphiques résident dans Reporting.

## Architecture non négociable

`Fait métier → Pièce justificative et statut → Écriture de comptabilité générale validée (si exigée) → Imputation/ventilation analytique traçable → Mesures de reporting et comparaison → Drill-down aux opérations d'origine`

- Ne jamais transformer un encaissement en chiffre d'affaires une seconde fois. Séparer **vente**, **prestation réalisée**, **encaissement** et **imputation analytique**.
- Ne pas affecter arbitrairement au véhicule les charges non attribuables ; permettre une section « non affecté » et une réconciliation expliquée.
- Séparer **agence de vente**, **agence d'exploitation**, **caisse qui encaisse**, **lieu de départ** et **agence du propriétaire** (si pertinent).
- Ne pas confondre **résultat analytique du véhicule**, **résultat contractuel du propriétaire** et **solde de son compte auxiliaire**.
- Tous les chiffres publiés sont **liés à une période, un périmètre, une date de fraîcheur, un statut de clôture et une définition métier**.
- Sous coupure de réseau, le siège affiche des chiffres provisoires ; chaque agence conserve sa comptabilité et ses faits locaux, avec synchronisation idempotente et corrections historisées.

## Interface cible

```
GESTION COMPTABLE
├── Comptabilité générale
│   └── Plan comptable • Tiers • Journaux • Balance • Bilan • Grand livre • Clôture
└── Comptabilité analytique
    ├── Véhicules (résultats, recettes/charges, voyages, historiques)
    └── Propriétaires (portefeuille, résultats, commissions, avances, règlements)

REPORTING ET ANALYSES
├── Vue d'ensemble et indicateurs
├── Performances des véhicules
├── Performances des agences
├── Comparaisons de périodes
├── Classique / VIP et lignes
├── Partenaires (vue directionnelle autorisée)
├── Rapports journaliers et clôtures d'agence
└── Exports / rapports programmables (si fonction disponible)
```

Les éléments de Reporting sont des **vues, regroupements ou filtres d'un même modèle analytique**. Ne pas fabriquer de comptabilité parallèle ni dupliquer les écritures.

## Références à lire selon la tâche

- [01 — Modèle de référence et frontières comptables](references/01-principes-et-sources.md)
- [02 — Dictionnaire des indicateurs et granularités](references/02-catalogue-kpi-et-granularites.md)
- [03 — Comparaisons, périodes et axes](references/03-filtres-et-comparaisons.md)
- [04 — Modèle de données et moteur de reporting](references/04-modele-donnees-et-moteur-rapport.md)
- [05 — Réconciliations et comptes de propriétaires](references/05-reconciliation-cloture-et-partenaires.md)
- [06 — Interfaces, tableaux simples, exports](references/06-interface-tables-export.md)
- [07 — Sécurité, performance, synchronisation](references/07-offline-securite-performances.md)
- [08 — Audit, tests et phases de déploiement](references/08-tests-acceptation-et-plan-claude-code.md)
- [Exemple de présentation comparative](examples/maquette_reporting_comparatif.html)

Se coordonner avec `/erp-transport-comptabilite-generale-analytique`, `/erp-transport-plan-analytique`, `/erp-transport-rapport-journalier-agence`, `/erp-transport-caisses-multi-agences` et `/erp-transport-afrique-centrale` ; si des consignes anciennes contradictoires existent, cette décision tranche les responsabilités du reporting, **sans supprimer les données historiques**.

## Méthode demandée à Claude Code

1. **Auditer sans rien modifier** le dépôt, le schéma SQL, les écrans, les schémas de vente, les contrats, les soldes, les règles d'imputation, les APIs, les tests, les exports et le moteur de sync. Nommer les fichiers réellement trouvés ; tableau existant/partiel/absent.
2. Proposer une architecture minimale **réutilisant** le plan analytique et les écritures existantes ; aucun second système concurrent.
3. Définir le dictionnaire des KPI, les calendriers et les périodes, le statut provisoire/définitif, la source de vérité et la traçabilité des montants.
4. Implémenter progressivement : données et réconciliation, API, tableaux et filtres, exports, comparaisons, drill-down, tests. Sauvegarde et migrations additives avant modification de données.
5. Démontrer les invariants : pas de doubles ventes, pas de double chiffre d'affaires, pas de transfert caisse compté en produit, séparation des profits et soldes partenaires, conformité des accès.
6. Livrer un compte rendu honnête : modifications faites, migrations appliquées, tests exécutés, écarts et validations métier/comptables restant à obtenir.

## Critères de fin

- Comparaison deux périodes arbitraires (mois, trimestre, année, période libre) pour véhicules/agences, avec valeur N, valeur N-1, écart absolu et pourcentage lorsque défini.
- Filtre combiné agence exploitation, agence vente, Classique/VIP, véhicule, propriétaire à date, ligne, voyage, dates et statut ; aucune fuite entre compagnies.
- Synthèse par véhicule = détail imputé et total réconciliable ; propriétaire = somme des périodes de contrats concernés, **pas** somme de tous les véhicules actuels sur tout l'historique.
- Le reporting signale les agences non synchronisées et les périodes non clôturées ; les états clos sont reproductibles avec le même périmètre et version de calcul.
- Rapports jour agence simples et imprimables ; reporting avancé distinct, graphiques optionnels, tableaux prioritaires.

## Invite d'exécution

« Applique `/erp-transport-reporting-analytique` dans mon dépôt ERP Transport. D'abord audite le projet existant ; ensuite fais reposer les états comparatifs et le reporting sur le plan analytique relié à la comptabilité générale et aux opérations métier. Conserve les deux sous-modules Comptabilité générale / Comptabilité analytique et uniquement deux familles analytiques principales Véhicules / Propriétaires. Crée reporting par agence, véhicule, gamme Classique/VIP et périodes avec KPI documentés, filtres, exports, drill-down, réconciliation comptable et statut des agences offline. Ne duplique aucune écriture ni recette ; préserve code et données existants, crée migrations additives et tests, et liste les modifications réellement effectuées. »
