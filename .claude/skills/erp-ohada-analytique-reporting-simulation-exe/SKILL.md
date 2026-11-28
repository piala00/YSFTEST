---
name: erp-ohada-analytique-reporting-simulation-exe
version: 2.0.0
description: "Auditer puis faire évoluer les ERP OHADA Commercial et Transport : plan comptable à sept chiffres, modules comptabilité générale et analytique, dix plans analytiques Transport, reporting multidimensionnel réconcilié, simulation de plusieurs mois et packaging Windows complet. À utiliser sur les sources réelles existantes."
---

# Skill Claude — ERP OHADA Commercial & Transport | Architecture et évolution

## Objectif

Réaliser dans **les deux ERP** Commercial et Transport, ou dans l'application intégrée si un seul dépôt les regroupe, les besoins décidés par l'utilisateur. **Ne pas recréer le logiciel, ne pas écraser ses fonctionnalités existantes, ne pas toucher aux données de production sans approbation.** L'archive jointe est une **spécification d'intégration pour Claude**, pas l'application modifiée. Les plans, modèles et API détaillés sont des propositions à adapter après audit du dépôt actuel.

### Décisions utilisateur non négociables

1. Tous les nouveaux comptes généraux d'entreprise ont **exactement sept chiffres**, sans changer la signification SYSCOHADA. La migration des comptes historiques est une opération distincte et contrôlée ; numéros incompatibles ou collisions bloquants, jamais de fusion automatique.
2. Deux modules distincts sur **chaque accueil** : **Comptabilité générale** et **Comptabilité analytique**. Les écritures monétaires n'existent qu'en comptabilité générale. L'analytique repose sur les écritures validées et les allocations/attributs explicites.
3. **Transport : dix plans analytiques visibles** (décision la plus récente) et une liste de sections par plan. Véhicules et Propriétaires de véhicules sont les deux **favoris**, pas les deux seuls plans. Cette instruction annule l'ancienne limitation du précédent Skill à deux rubriques.
4. **Commercial : plusieurs plans configurables** selon l'entreprise (agences, magasins, commerciaux, clients, familles d'articles, etc.). Ne pas imposer artificiellement les dix plans Transport.
5. **Reporting général + analytique complet et cohérent**, multi-plans, multi-périodes, comparaisons, états détaillés, drill-down vers pièce, exports et habilitations.
6. **Simulation opérationnelle de plusieurs mois consécutifs** dans un **dossier isolé**, en conservant l'état d'un mois sur l'autre (stock, trésorerie, créances, contrats, paie...). Ajouter une **simulation prévisionnelle par scénarios** séparée, sans générer d'écritures réelles.
7. **Compilation Windows de l'ensemble du client ERP** avec un point d'entrée clair `ERP_OHADA.exe`; inclure tous les modules accessibles, ressources et dépendances nécessaires. Proposer la distribution réellement autonome adaptée à l'architecture (client connecté vs serveur local intégré). Une base SQL Server/PostgreSQL distante, Render ou les services réseau ne se « compilent » pas magiquement dans l'EXE.

## Source de vérité et séparation des responsabilités

- **Générale** : écriture validée, compte à 7 chiffres, journal, exercice, tiers, pièce, date comptable.
- **Analytique** : référence à la ligne générale + plans/sections + ventilation. Pas de second grand livre indépendant ou de saisie parallèle de produits/charges.
- **Reporting** : appelle les mêmes services de calculs généraux/analytique, ajoute filtres/visualisation/comparaisons ; pas de seconde base de montants faisant autorité.
- **Simulation opérationnelle** : utilise les opérations réelles du moteur dans une base fictive étiquetée `SIMULATION` ; pas de production.
- **Prévision/what-if** : écrit uniquement dans son espace de scénarios, pas dans `Ecriture`/`LigneEcriture` de production.
- **Client Windows/Web** : même API et mêmes droits par utilisateur/société/site, présentation adaptée mais règles identiques.

## Méthode impérative

1. **Lire dans l'ordre** les fichiers `references/ETAT_ACTUEL_VERIFIE.md`, `references/PLANS_ANALYTIQUES.md`, `references/ARCHITECTURE_CIBLE.md`, `references/REPORTING_ET_ETATS.md`, `references/SIMULATION_MULTI_MOIS.md`, `references/COMPILATION_WINDOWS.md`, `references/PLAN_REALISATION_ET_TESTS.md`. Utiliser `CATALOGUE_ETATS.csv` comme backlog d'états et non comme liste de fonctionnalités déjà disponibles.
2. Inventorier le **dépôt réel** et comparer aux sources d'archive du 26/10/2026. L'état du dépôt peut avoir évolué. Identifier les modules, modèles, migrations, tests, droits et moteurs déjà fonctionnels ; documenter les écarts.
3. Implémenter par **migrations compatibles et incrémentales** ; préserver les sept chiffres, les droits, la multi-société et toutes les fonctions métiers existantes.
4. Implémenter d'abord moteur analytique + contrôles de rapprochement, ensuite catalogues et API reporting, ensuite UX, ensuite simulation multi-mois, ensuite scénario prévisionnel, enfin packaging EXE. Garder chaque étape démontrable.
5. Exécuter des tests automatisés unitaires/intégration + parcours Web/Windows ; tester sur **copie de base anonymisée**, jamais sur données réelles destructivement.
6. Livrer les fichiers modifiés, migrations, exemples de commandes, résultat vrai des tests, liste des inconnues, artefacts finaux uniquement s'ils ont réellement été construits et vérifiés. Ne pas annoncer un EXE fonctionnel avant test sur Windows.

## Comptabilité : exactitude

- Comparer les agrégations par **plan analytique**, jamais sommer les mêmes montants entre deux plans (une écriture peut appartenir à plusieurs plans sans doubler le résultat de la société).
- À l'intérieur d'un plan, allocations d'une ligne et résiduel non affecté doivent totaliser **100 % au maximum** ; politiques de ventilation pour atteindre 100 % si le plan est requis ; coûts partagés explicitement répartis et traçables.
- Rapprochements `total général = affecté + non affecté` pour produits et charges et pour chaque période/plan. Comptes d'exploitation vérifiables jusqu'aux pièces.
- Distinguer **résultat économique d'un véhicule**, **rémunération contractuelle du propriétaire** et **solde à payer au propriétaire** (compte de tiers).
- Calculs en `Decimal`, montants en XAF, arrondis déterministes et conservation des traces.
- Les écritures en brouillard ne sont pas incluses dans les états comptables officiels par défaut ; proposer une option explicitement étiquetée « brouillard » si autorisée.

## Frontières et réserves

L'archive inspectée concerne le **client Windows commercial** contenant aussi des composants Transport. Elle ne prouve ni l'état d'un dépôt Transport indépendant ni l'état actuellement déployé sur Render. Aucune modification de code ou compilation n'est réalisée par **ce Skill lui-même**. Le contrôle documentaire OHADA/SYSCOHADA et fiscal 2026 doit être fait séparément avant de qualifier les états légaux de conformes.

## Inventaire

- `references/ETAT_ACTUEL_VERIFIE.md` : observations concrètes tirées des archives inspectées.
- `references/ARCHITECTURE_CIBLE.md` : contrats de données et règles de calcul.
- `references/PLANS_ANALYTIQUES.md` : les dix plans Transport et axes configurables Commerce.
- `references/REPORTING_ET_ETATS.md`, `references/CATALOGUE_ETATS.csv` : UX et catalogue d'états.
- `references/SIMULATION_MULTI_MOIS.md` : simulation opérationnelle et prospective.
- `references/COMPILATION_WINDOWS.md` : plan de compilation et de livraison.
- `references/PLAN_REALISATION_ET_TESTS.md`, `references/CONTROLES.csv` : tâches et acceptation.
- `references/INCONNUES.md`, `references/SOURCES.md` : informations restant à vérifier et sources techniques.
- `references/legacy/PATCH_SEPT_CHIFFRES_COMMERCE.patch` : **ancien correctif facultatif** fourni pour référence ; ne pas appliquer sans comparaison du dépôt et pré-contrôle, et surtout ne pas réintroduire la limitation analytique à deux plans.

Consigne : préserver les deux modes de déploiement **Web Django/Render** et **Bureau Windows**. Pour la compilation, tester l'autonomie sur une machine Windows propre ; le serveur central distant est explicitement une dépendance d'exploitation, pas un fichier à fusionner.
