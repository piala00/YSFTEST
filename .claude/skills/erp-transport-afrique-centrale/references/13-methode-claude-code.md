# 13 — Guide de travail pour Claude Code : projets déjà commencés

## Démarrage obligatoire par audit du dépôt réel

**Contexte :** l'utilisateur développe déjà cet ERP avec Claude. Ne présume pas que ce dépôt est vide, ni que FastAPI, PostgreSQL ou une autre stack y sont effectivement installés. Avant de toucher au code :

1. `pwd`, inspection des dossiers, recherche des points d'entrée, `README`, `CLAUDE.md`, configs, tests, migrations, mécanismes authentification et connexion bases.
2. Établir une cartographie réelle des modules existants, modèles de données, événements, rôles, écrans, APIs, tâches programmées, installations agences/siège.
3. Comparer aux 14 référentiels de ce skill ; produire tableau priorisé `existant / partiellement présent / manquant / incohérent`, avec références précises au code.
4. Préserver le fonctionnement et l'apparence validés par l'utilisateur ; demander arbitrage seulement en cas de choix métier véritablement bloquant ; sinon choisir une solution non destructive et documenter l'hypothèse.
5. Produire des spécifications testables et un plan de migration incrémental. Ne jamais commencer par « tout réécrire ».

## Workflow répétable par demande

**1. Contrat métier :** spécifier qui déclenche l'action, pourquoi, agence, véhicule/voyage/tiers concernés, préconditions, validations, droits, écrans, documents, statuts, erreurs et corrections.

**2. Flux comptables et analytiques :** détailler paiement réel vs créance, comptes symboliques, règles SYSCOHADA à faire valider, coût direct/indirect, partenaire, reporting.

**3. Données / API :** migrations, contraintes, endpoint/application service, transactional outbox, consumers idempotents, audit, scope multi-tenants.

**4. Interface utilisateur :** proposer module du service ; vues de listes, recherche/filtrage, édition, validation, droits, impression, statut sync ; ne pas introduire d'appels du client directement à une base SQL centrale.

**5. Vérification :** tests unitaires/intégration end-to-end, concurrence, perturbation LAN/WAN, sécurité, calcul, état après retry/compensation, référentiels.

**6. Livraison :** résumé des changements, fichiers modifiés, migrations, tests exécutés/résultats, risques non réglés et prochaine phase recommandée.

## Ordre de mise en œuvre conseillé

- Socle : tenants/sociétés/agences, rôles, authentification, audit, référentiels véhicules/partenaires et synchronisation événementielle minimale.
- Billetterie : trajets, tronçons, plans de sièges, quotas, vente, caisses, contrôle anti-double usage.
- Messagerie : chaîne custody, colis, véhicule/voyage, suivi, paiements.
- Exploitation : planification, équipes, trajets, feuille de route, clôture.
- Garage, achats, stocks, carburant : coûts et immobilisations.
- RH/paie : dossiers, présences, habilitations, paie, avances, journal.
- Comptabilité/trésorerie : moteur SYSCOHADA, sous-livres, automatisations, rapports.
- Propriétaires : contrats, décomptes, relevés, portail sécurisé.
- Multi-sites : observabilité, intégration, sauvegardes, migration, reporting direction.

**Note :** le moteur comptable, la traçabilité et la synchronisation *squelettes* doivent exister dès le départ, même si l'ensemble des sous-modules est développé en phases.

## Proposition de structure logique de code, sans imposer le renommage

```text
backend/
  core/identity,tenancy,permissions,audit,events,sync
  domains/booking,ticketing,parcel,operations,fleet,workshop,inventory,fuel
  domains/hr,payroll,partners,treasury,accounting,analytics
  reporting/agency,vehicle,trip,partner
  integrations/devices,payments
frontend/
  modules/ticketing,parcels,operations,garage,hr,finance,partners,management
infra/
  agency-node,head-office-node,backups,monitoring
migrations/
tests/unit,integration,e2e,offline,concurrency,security
```

Les chemins sont des **suggestions de séparation logique**, pas une instruction de déplacement destructif du dépôt.

## Prompt de démarrage conseillé à Claude Code

> Utilise le skill `/erp-transport-afrique-centrale`. Commence par auditer le dépôt actuel, sans modifier ni supprimer aucun fichier. Produis une matrice entre les fonctionnalités existantes et le référentiel : modules des services, cycle comptable automatique, analytique par voyage/véhicule, partenaires propriétaires, RH-paie, fonctionnement hors ligne, synchronisation et rapports d'agence/siège. Indique ensuite un plan de développement incrémental priorisé avec tests. Ne commence l'implémentation d'un chantier que dans le périmètre que je valide.

## Livrables standards pour tout chantier

- Carte responsabilités des services et leurs échanges.
- Modèles relationnels et migrations documentées.
- Liste d'événements et consommateurs, avec at-least-once et idempotence.
- Matrice permission + contexte d'agence/société/propriétaire.
- Schémas de comptabilisation symboliques à faire valider, et imputation analytique.
- UX, droits, imprimés et règles métier.
- Tests d'acceptation avec preuves de résultat ; risques/restes.

## Critères de non-régression

Le guichetier continue à vendre et imprimer quand Internet est coupé ; l'agent de colis ne voit pas la paie ; le garage fait des pièces et OR sans être le comptable ; le chauffeur rapproche ses avances ; le comptable récupère des opérations contrôlées depuis tous les services ; la direction suit chaque agence et véhicule ; le partenaire ne consulte que son compte ; aucune duplication à la reconnexion.
