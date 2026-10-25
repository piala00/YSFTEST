---
name: erp-transport-afrique-centrale
description: Référentiel de conception, audit et développement d'un ERP modulaire de transport interurbain et messagerie multi-agences en Afrique centrale (Cameroun/OHADA), avec billetterie, colis, garage, voyages, véhicules partenaires, RH-paie, comptabilité et synchronisation offline-first. À utiliser pour toute modification de ce projet dans Claude Code.
---

# ERP Transport Afrique Centrale — référentiel directeur pour Claude Code

## 1. Mission du skill

Concevoir, auditer, faire évoluer et tester un **ERP multi-compagnies, multi-agences, multi-services, multi-véhicules et multi-partenaires** pour les transporteurs interurbains du Cameroun et, par extension, de l'Afrique centrale. Chaque service exerce son métier dans **son propre module** et selon **ses autorisations**, tandis que le système **rassemble automatiquement** et **sans double saisie** les faits dans les caisses, la comptabilité, la gestion analytique de chaque véhicule, les résultats de chaque agence et la supervision centrale.

Ce skill est un **référentiel de réalisation**, pas la preuve que les fonctionnalités existent déjà dans le dépôt. Le projet a commencé avec Claude : **ne jamais remplacer ou refondre l'existant sans audit du code et accord explicite**. Ne pas inventer de fonctionnalités implémentées ni de conformité légale.

## 2. Invariants non négociables

1. **Décentralisation opérationnelle** : chaque agence peut exécuter ses opérations autorisées sur sa base locale, sans Internet. La coupure d'électricité nécessite une alimentation de secours ; aucune garantie 24/7 sans électricité et matériel adaptés.
2. **Organisation par service** : billetterie ; messagerie-colis ; exploitation/voyages ; garage/maintenance ; carburant ; stocks/achats ; RH/paie ; caisse/trésorerie ; comptabilité ; partenaires ; direction ; administration. Les postes ne doivent voir que leurs droits.
3. **Une opération, plusieurs effets contrôlés** : un acte métier produit des effets automatiques dans les sous-ledgers concernés, jamais une double saisie manuelle. La génération d'écritures respecte un schéma comptable paramétré, la date comptable, les validations et la responsabilité de l'entreprise.
4. **Traçabilité multidimensionnelle** : toute recette/charge rattachable porte les dimensions `tenant_id`, `legal_entity_id`, `agency_id`, `service_id`, et, si applicables, `trip_id`, `vehicle_id`, `partner_id`, `route_id`, `employee_id`, `cost_center_id`, `source_document_id`.
5. **Véhicule comme centre analytique**, et **voyage comme unité d'exploitation**. Le résultat par véhicule doit intégrer toutes ses recettes et ses coûts selon les règles explicites d'attribution et de répartition ; ne jamais supposer qu'une dépense d'agence est automatiquement une dépense de véhicule.
6. **Partenaire propriétaire** : dissocier résultat analytique du véhicule, résultat contractuellement attribuable, solde dû au partenaire, règlements effectués et solde de son compte auxiliaire. Propriété/contrat historisés par dates d'effet.
7. **Comptabilité générale en partie double**, conforme au référentiel SYSCOHADA applicable après validation des configurations par un professionnel ; pas de numéros de comptes, taux de cotisations, barèmes de paie ou règles de TVA inventés.
8. **Synchronisation sûre** : Transactional Outbox / Inbox, identifiants immuables globaux, idempotence, accusés de réception, reprise, rejets explicites, horodatage, états de synchronisation, conflits sensibles arbitrés sans perte.
9. **Inventaire des sièges partitionné** : les ventes hors ligne reposent sur des sièges, segments ou quotas attribués exclusivement. Aucune promesse impossible de prévention du surbooking global entre agences complètement déconnectées et non coordonnées.
10. **Billet antifraude** : QR signé et lié au voyage ; validation locale atomique par une autorité d'embarquement ; audit des scans ; un QR signé seul ne bloque pas la copie d'un billet authentique.
11. **Exploitation responsable** : changements financiers par annulation/contrepassation/versionnement, pas de suppression silencieuse ; clôtures signées et rouvrables uniquement par procédure tracée.
12. **Multi-sociétés/compagnies isolées** : étanchéité des données, des droits, des plans comptables, des bases et des journaux. Une agence dépend d'une société juridique ; ne pas confondre centralisation d'agences et consolidation légale de groupes.
13. **RH/paie réellement intégrées** : dossiers, contrats, affectations, temps/absences, paie, avances, retenues, paiements, écritures et coût analytique ; validation humaine de paie et respect des règles propres au pays.
14. **Rapport journalier de service → agence → siège** : produire états de ventes, colis, garages, voyages, caisses, équipages, paie et partenaires, avec statut *complet / provisoire / données manquantes*.
15. **Sécurité par défaut** : contrôle des autorisations côté serveur et dans les lectures SQL, journal d'audit, secrets hors dépôt, chiffrement des communications, sauvegardes testées.

## 3. Bibliothèque : lire seulement les documents utiles à la tâche

- [01 — Vision, organisation des services, frontières métier](references/01-vision-modules-services.md)
- [02 — Booking, billetterie, anti-double usage](references/02-billetterie-booking.md)
- [03 — Messagerie, expéditions et réception des colis](references/03-messagerie-colis.md)
- [04 — Exploitation, voyages, véhicules, garage et stocks](references/04-exploitation-flotte-garage.md)
- [05 — Ressources humaines, chauffeurs, convoyeurs et paie](references/05-rh-paie-equipages.md)
- [06 — Contrats et comptes des partenaires propriétaires](references/06-partenaires-proprietaires.md)
- [07 — Caisses, comptabilité SYSCOHADA et analytique](references/07-comptabilite-tresorerie.md)
- [08 — Chaîne d'automatisation interservices et règles d'événements](references/08-workflows-interservices.md)
- [09 — Offline-first, synchronisation, conflits et disponibilité](references/09-offline-sync.md)
- [10 — Modèle de données, API, droits et audit](references/10-data-api-acces.md)
- [11 — Clôtures, rapports par agence/véhicule et tableaux de bord](references/11-reporting-clotures.md)
- [12 — Tests de bout en bout et critères de réception](references/12-tests-acceptation.md)
- [13 — Méthode concrète de développement avec Claude Code](references/13-methode-claude-code.md)
- [14 — Références réglementaires et hypothèses à vérifier](references/14-reglementation-sources.md)
- [15 — Plan analytique Transport, axes Classique/VIP et rattachements interservices](references/15-plan-analytique-transport.md)
- [16 — Rapport journalier d’agence simplifié (tableaux recettes, bagages, sorties, caisse)](references/16-rapport-journalier-simple.md)
- [17 — Configuration des caisses par agence et consolidation sans doublons](references/17-caisses-multi-agences.md)

**Module spécialisé multi-caisses ajouté** : invoquer `/erp-transport-caisses-multi-agences` pour les agences mono/multi-caisses, les transferts internes, les sessions et la centralisation des soldes. Les caisses sont indépendantes des services producteurs.

**Module de rapports simples ajouté** : invoquer `/erp-transport-rapport-journalier-agence` pour les états quotidiens en tableaux de chaque agence, leur caisse et leurs reversements. Ne pas confondre montant des départs du jour avec encaissements du jour.

**Module spécialisé ajouté** : invoquer `/erp-transport-plan-analytique` pour l'audit et le développement des dix plans analytiques, le contrôle Classique/VIP et les imputations interservices. Les véhicules VIP et Classique sont distincts et dédiés ; aucune affectation de voyage incompatible ne doit être acceptée.

## 4. Procédure de travail dans le dépôt

**Avant toute édition :**

1. Inspecter arborescence, `README`, `CLAUDE.md`, schémas SQL/migrations, API, clients, tests et configuration de déploiement. Produire une cartographie **existant / absent / ambigu / dette technique**.
2. Identifier les modules touchés, le contexte `tenant/legal_entity/agency/vehicle/trip/partner`, les opérations source, les écritures et les rapports affectés.
3. Lire les références appropriées. Produire un mini-contrat fonctionnel : acteurs, entrées, validations, statuts, événements, débits/crédits paramétrés, dimensions analytiques, droits, mode hors ligne et critères de tests.
4. Vérifier la compatibilité avec le schéma et le stack existants ; proposer des migrations réversibles. Préserver les données et les interfaces existantes sans autorisation de rupture.
5. Implémenter en vertical slices : entités et contraintes → commandes métier transactionnelles → événements/outbox → comptabilité/intégration → API → écrans → rapports → tests.
6. Ne pas déduire une opération financière à partir d'un simple changement d'affichage. Tout mouvement doit provenir d'une action métier validée et traçable.
7. Exécuter les tests adaptés au dépôt (unitaires, intégration, permissions, concurrence, synchronisation, end-to-end) et rapporter précisément ceux qui ont été réellement exécutés et ceux qui restent à faire.
8. À la fin de chaque chantier, livrer une matrice : fonctionnalité / module producteur / autres modules alimentés / journal comptable / centre analytique / permissions / couverture des tests.

## 5. Règle d'intégration transversale

Pour chaque fait métier validé, raisonner sur le trajet :

`SERVICE D'ORIGINE → DOCUMENT SOURCE → ÉVÉNEMENT MÉTIER → SOUS-LEDGER/CAISSE/STOCK → ÉCRITURE COMPTABLE VALIDABLE → AFFECTATION ANALYTIQUE → RÉSULTAT VOYAGE/VÉHICULE → RAPPORT AGENCE → RAPPORT SIÈGE`

La comptabilité peut appliquer la validation requise avant comptabilisation définitive. La trésorerie ne doit être modifiée que par de **vrais mouvements de paiement**, pas par une simple commande, promesse ou facture impayée. Chaque événement portant une action monétaire doit définir sa source d'autorité, son cycle de vie et son mécanisme de correction.

## 6. Résultat demandé à Claude selon la requête

- **Conception** : diagramme des modules + rôles + flux interservices + modèle de données + états + règles de gestion + risques + tests.
- **Audit** : constat sourcé dans le dépôt, écarts au présent skill, risques classés, propositions sans altération destructive.
- **Développement** : changements concrets cohérents avec l'existant, migrations, tests d'intégration, permissions, écrans et historique.
- **Comptabilité/paie** : distinguer clairement les schémas proposés des règles validées par le professionnel habilité ; prévoir paramétrage pays, dates d'effet et audit.
- **Reporting** : exposer la provenance de chaque chiffre ; révéler les données non remontées ; permettre le drill-down vers les pièces.

## 7. Interdits

Aucune écriture SQL directe dans la base Sage ou une base tierce sans mandat et protocole explicites ; aucune réinitialisation des données ; aucun montant payé sans trace ; aucune réutilisation d'un `tenant_id` d'une autre compagnie ; aucun « dernier arrivé écrase tout » pour les montants, soldes, sièges ou propriétés ; aucune balance partenaire obtenue en confondant revenus, droits contractuels et trésorerie ; aucun résumé global qui masque les opérations en attente de synchronisation.
