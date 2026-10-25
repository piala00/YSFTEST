---
name: erp-transport-comptabilite-generale-analytique
description: Mise à jour du projet ERP Transport Afrique Centrale pour séparer deux modules comptables visibles, la Comptabilité générale de toute la société et la Comptabilité analytique à deux rubriques de restitution (Véhicules et Propriétaires), avec alimentation automatique depuis billetterie Classique/VIP, colis, bagages, garage, paie, caisses, voyage, règles OHADA, contrats et synchronisation offline-first. À utiliser pour développer, auditer ou modifier les comptes, balances, rapports, partenaires ou imputations de transport.
---

> **DÉCISION COMPTABLE PRIORITAIRE (25/10/2026) :** toute ligne analytique MONÉTAIRE doit obligatoirement dériver d'une ligne comptable GÉNÉRALE préalablement validée/postée, avec référence traçable. La comptabilité analytique ne peut créer des recettes, dépenses, dettes ni créances indépendantes. Voir `/erp-transport-comptabilite-source-unique` ; il prévaut sur les anciennes formulations contraires. Les KPI non monétaires restent issus de l'exploitation.


# Skill Claude Code — Comptabilité générale et analytique (Véhicules + Propriétaires)

## Décision métier utilisateur — prioritaire

**Gestion comptable comporte EXACTEMENT deux sous-modules métier visibles au premier niveau :**

1. **COMPTABILITÉ GÉNÉRALE** : toutes les sociétés concernées et, pour chaque société, toutes ses agences et tous ses services. Plan comptable SYSCOHADA applicable, tiers, journaux, pièces, balances, grand livre, bilan, compte de résultat, trésorerie, rapprochements, clôtures. Ne pas confondre la centralisation des établissements d'une seule société avec une consolidation légale de groupes distincts.
2. **COMPTABILITÉ ANALYTIQUE** : **deux seules rubriques centrales de restitution** : **VÉHICULES** et **PROPRIÉTAIRES DE VÉHICULES**. Tous les états, analyses et parcours centraux sont organisés autour de ces deux pivots. Les autres critères (agence, gamme CLASSIQUE/VIP, service, ligne, activité, voyage, contrat, canal de vente) restent des **dimensions techniques d'affectation et des filtres** ; ce ne sont pas des rubriques analytiques principales supplémentaires présentées à l'utilisateur.

Cette décision **précise et remplace la navigation de reporting** proposée dans `/erp-transport-plan-analytique` où 10 plans étaient listés. **Elle n'ordonne PAS de supprimer les 10 dimensions de données préexistantes**, nécessaires aux ventilations et analyses croisées ; les préserver et les masquer sous configuration/filtres. Si un nom "plan analytique" est réservé à une table ou un référentiel, conserver sa sémantique SQL existante et documenter la traduction vers les 2 pivots métiers.

## Règles immuables

- Chaque service garde sa propre interface opérationnelle ; il produit des pièces sources et événements. Les **deux comptabilités sont alimentées automatiquement**, sans ressaisie d'un montant.
- Une écriture du grand livre et sa ventilation analytique ne représentent **qu'une opération économique**, jamais deux recettes/charges ou deux encaissements.
- **Un véhicule est rattaché à un propriétaire ou à un contrat valide à la date du fait concerné**, avec traçabilité des réaffectations, y compris véhicules de la compagnie. Ne jamais attribuer rétroactivement des résultats à un nouveau propriétaire.
- **Un propriétaire peut posséder plusieurs véhicules** ; une vue véhicule détaille chaque engin, une vue propriétaire agrège uniquement le portefeuille et les périodes qui lui appartiennent contractuellement.
- CLASSIQUE et VIP = **flottes de véhicules distinctes et dédiées**. La gamme du voyage doit être cohérente avec l'affectation historique du véhicule. Filtrer par gamme depuis les deux rubriques analytiques.
- Les bagages voyageurs payants, les billets et les colis sont des activités différentes. Les montants sont attribués au véhicule/voyage ayant réalisé le transport ou selon une règle de partage documentée ; ne jamais confondre vente dans une agence et exploitation du véhicule.
- **La caisse du service ≠ le service ≠ l'agence ≠ le véhicule** ; une agence peut avoir une caisse commune ou plusieurs caisses. Le règlement n'est pas la facture et le transfert interne n'est pas une nouvelle recette.
- Un compte d'exploitation **analytique** de véhicule ≠ compte courant du propriétaire ≠ montant à lui payer : les règles de partage dépendent du contrat, du rôle de la compagnie (principal/intermédiaire), des charges imputables et des règlements.
- Un véhicule peut avoir coûts sans voyage (garage, assurance). Une dépense de siège non imputable au véhicule reste en comptabilité générale ; ne jamais forcer artificiellement toutes les charges sur les véhicules.
- Le système est **offline-first** : une écriture en attente de synchronisation ne doit pas être dupliquée ; toute situation incomplète est datée et marquée provisoire. Ne pas appliquer « last write wins » aux montants financiers.
- Les numéros de comptes SYSCOHADA, schémas fiscaux, règles de reconnaissance des produits et commissions doivent être **paramétrables et validés par un professionnel compétent**, non inventés par Claude.

## Navigation fonctionnelle à appliquer

```
GESTION COMPTABLE
├── Comptabilité générale
│   ├── Tableau de bord société
│   ├── Plan comptable et tiers
│   ├── Journaux / saisies / écritures
│   ├── Encaissements, règlements et rapprochements
│   ├── Balance / Grand livre / Bilan / Compte de résultat
│   └── Clôture et contrôle
└── Comptabilité analytique
    ├── Véhicules
    │   ├── Liste / recherche / filtres (période, gamme, agence, etc.)
    │   ├── Compte d'exploitation du véhicule
    │   ├── Voyages, recettes, coûts et pièces sources
    │   └── Historique et résultat détaillé
    └── Propriétaires
        ├── Liste des partenaires / flotte détenue
        ├── Résultats des véhicules du propriétaire
        ├── Situation contractuelle et compte auxiliaire lié
        └── États, relevés, avances, retenues et règlements
```

Les écrans techniques « plans », « sections », « clés de ventilation » et « règles d'imputation » demeurent accessibles aux profils autorisés **en paramètres avancés**, pas comme une troisième rubrique de restitution analytique.

## Références à lire avant le développement

1. [Spécifications fonctionnelles : 2 modules et 2 pivots](references/01-organisation-modules-et-interfaces.md)
2. [Chaînes d'opérations et imputations automatiques](references/02-flux-metier-vers-comptabilites.md)
3. [Modèle de données, relations et migrations conservatrices](references/03-modele-donnees-et-migrations.md)
4. [États analytiques simples par véhicule/propriétaire](references/04-etats-et-rapports.md)
5. [Contrats, calculs, solde partenaire et cas particuliers](references/05-comptes-partenaires-et-contrats.md)
6. [Écritures, rapprochement, OHADA et clôtures](references/06-comptabilite-generale-et-controles.md)
7. [Offline-first, RBAC et confidentialité](references/07-offline-securite-et-permissions.md)
8. [Critères d'acceptation et plan de livraison Claude Code](references/08-tests-et-methode.md)
9. [Exemple de rapports tabulaires](examples/rapport_analytique_vehicules_proprietaires.html)

## Exécution dans le dépôt utilisateur

1. **Auditer le dépôt avant modification** : examiner modèles/DAO, migrations, schéma, système de permissions, historique des véhicules, recettes, dépenses, caisse, partenaires, voyages, comptabilité générale, analytique, clôture et synchronisation. Produire tableau `existant/partiel/absent/incompatible`, avec noms des fichiers réels.
2. Relever les **règles de comptabilisation déjà implémentées** ; identifier les doublons entre événements sources, écritures comptables, mouvements de caisse et mesures analytiques. Aucune migration destructive ; sauvegarde et tests de reprise avant toute migration.
3. Réorganiser la **navigation** pour deux sous-modules puis, dans l'analytique, uniquement deux rubriques principales (Véhicules, Propriétaires), sans supprimer les dimensions analytiques ni les APIs utiles.
4. S'appuyer sur les pièces sources et contrats datés ; créer ou adapter les écritures de grand livre et imputations via moteur versionné et idempotent. Préférer l'extension du système existant plutôt qu'une architecture parallèle concurrente.
5. Développer les rapports véhicule (résultat, mouvements) et propriétaire (portefeuille, résultat + rapprochement compte courant). Conserver un drill-down vers facture, billet, bordereau de colis, bon de garage, paie, paiement et justificatifs.
6. Intégrer les agences mono-/multi-caisses ; séparer journée de départ, journée d'encaissement et période comptable. Réconcilier totaux et marquer fraîcheur des données par agence.
7. Exécuter tests par cas métier, concurrence et synchronisation, documenter résultats réels ; ne pas prétendre avoir modifié le projet si seules les spécifications sont fournies.
8. Résumer précisément fichiers/migrations réalisés, comportement avant/après, choix comptables à faire valider, échecs et limitations.

## Définition de terminé

- Menu Gestion comptable = **2 sous-modules**. Analytique = **2 entrées de restitution** Véhicules et Propriétaires.
- Un billet, bagage, colis, carburant, pièce consommée, charge salariale affectable ou frais de garage apparaît à la bonne période et au bon véhicule, une seule fois.
- Un propriétaire détenant plusieurs véhicules obtient résultat et historique par véhicule puis total agrégé, avec montant dû et paiements distincts.
- Le module général contient **toutes** les opérations comptabilisables de la société, y compris celles qui n'ont aucun véhicule.
- Les filtres agence, gamme Classique/VIP, ligne, voyage et dates existent sans créer de modules de résultat concurrents.
- Compta analytique véhicule et comptes partenaires sont rapprochables avec écritures GL/sous-livres, et les écarts explicables.
- Coupures réseau, retours de synchro, annulations et rectifications ne dupliquent jamais un montant.

## Commande suggérée

« Applique `/erp-transport-comptabilite-generale-analytique` dans mon dépôt ERP Transport. Audite le code existant, conserve les données et crée deux modules de Gestion comptable : la générale sur toute la société et l'analytique avec exactement deux rubriques Véhicules et Propriétaires. Les autres dimensions servent à l'imputation et aux filtres. Relie automatiquement tous les services, conserve les flottes Classique/VIP distinctes, les caisses par agence, les contrats partenaires et la synchronisation offline-first. Implémente les tests et rends compte des fichiers réellement modifiés. »


## Complément — Reporting décisionnel distinct

La restitution Comptabilité analytique demeure limitée à **Véhicules** et **Propriétaires**, tandis que le module transversal **Reporting et Analyses** peut présenter des comparaisons par agence, période, gamme, ligne et service en réutilisant le plan analytique commun. Ne pas implémenter une nouvelle comptabilité ou un second moteur de résultat. Voir `/erp-transport-reporting-analytique`.
