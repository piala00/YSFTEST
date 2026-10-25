# 01 — Vision métier, services indépendants et coopération automatique

## Objectif et périmètre

ERP destiné à une **compagnie de transport interurbain** : agences (gares routières et représentations), transport de personnes, messagerie, garage, flotte, chauffeurs/convoyeurs, propriété propre ou partenaires, comptabilité et paie. Multi-compagnies isolées, multi-sociétés éventuelles, multi-pays configurables. Distinguer service opérationnel, département, centre de coûts et société juridique.

**Principe fondateur utilisateur :** chaque agent ouvre la même plateforme, n'y voit que les fonctions autorisées pour son rôle et son agence et travaille normalement ; à l'arrière-plan, les modules contribuent aux états de la caisse, de la comptabilité, du voyage, du véhicule, du partenaire, de l'agence et du siège. L'agent de garage n'a pas à saisir une deuxième fois la dépense en comptabilité : il crée une demande ou facture, puis le circuit achats/caisse/comptabilité la traite avec contrôles appropriés.

## Cartographie des modules et responsabilités

| Service | Module, postes et responsabilité principale | Pièces sources | Consommateurs automatiques |
|---|---|---|---|
| Guichet | Billetterie, réservation, émission, reports, remboursements | réservation, ticket, reçu, note d'annulation | siège, caisse, voyage, statistique, comptabilité |
| Contrôle | Scan et embarquement, manifeste, clôture | scan, statut billet, manifeste | exploitation, reporting, litiges |
| Messagerie | Réception et remise de colis, transferts et incidents | lettre de voiture/expédition, preuve de livraison | caisse, voyage, agence destinataire, comptabilité |
| Exploitation | Planification des lignes, voyages, véhicules, équipes | affectation, feuille de route, ordre de départ, compte rendu | billetterie, colis, flotte, analytique |
| Garage | Entretien, diagnostics, travaux et coûts | ordre de réparation, bon de sortie pièces, facture | stock, immobilisations ou charges, véhicule, fournisseurs |
| Carburant | Bons carburant et consommation | bon, tickets station, compteur/km | caisse, véhicule, voyage, indicateurs |
| Achats/stocks | Pièces, pneus, consommables, approvisionnements | commande, réception, facture, sortie | garage, comptabilité, fournisseurs |
| Personnel/RH | Dossiers, contrats, présence, planning, congés | contrat, pointage, congé, fiche de paie | exploitation, coûts, comptabilité, banque |
| Caisses/trésorerie | Sessions, encaissements, dépenses, remises, avances | pièces de caisse, quittances, rapprochement | comptabilité, contrôle des recettes |
| Comptabilité | Paramétrage, validation, écritures, taxes, rapprochement | pièces centralisées, journaux, OD | balance, bilan, résultats, audits |
| Partenaires | Propriétaires, contrats, rémunérations, règlements | contrat, relevé, décompte, paiement | analytique véhicule, auxiliaire, trésorerie |
| Direction | KPI, alertes, stratégie, clôtures, contrôle interne | rapports certifiés, états analytiques | décisions et supervision |
| Administration | Agences, rôles, paramètres, audit, synchronisation | autorisations, logs, configurations | tous avec limites strictes |

Chaque module présente au minimum : **Tableau de bord / Opérations / Documents / Recherche-Listes / Rapports / Paramètres de service** (les Paramètres selon permission), avec navigation cohérente. Les onglets ne constituent pas des frontières de sécurité : la séparation est garantie sur API, règles de données et base.

## Référentiels partagés

- `compagnie / société légale / établissement / agence / service / guichet` : identités et hiérarchies avec dates d'effet.
- `personne / client / expéditeur / destinataire / partenaire / salarié / fournisseur` : rôles métiers séparés ; un tiers peut remplir plusieurs rôles avec autorisations et masquage de données.
- `véhicule / propriétaire / contrat / ligne / arrêts / tronçon / voyage / équipage`.
- `produit/service tarifé / grille tarifaire / moyen de paiement / devise / taxes` avec dates d'effet.
- `plan comptable / journaux / axes analytiques / centres de coûts / règles de ventilation / calendriers de clôture`.

## Documents et états normalisés

Chaque pièce possède identifiant immutable, numéro métier lisible propre à son espace (`tenant + legal_entity + agency + type + série`), date réelle et comptable, auteur, agence d'origine, statut, version, pièces justificatives, total/devise et chaîne d'audit. **Ne jamais utiliser seulement un entier auto-incrémenté local comme identifiant global.** Les statuts doivent être explicites et les annulations tracées.

## Équilibres indispensables

- Une agence A peut vendre un billet pour un véhicule exploité depuis l'agence B. Les faits d'**encaissement**, **vente commerciale**, **transport effectif** et **rémunération du propriétaire** relèvent de dimensions différentes : ne pas tout imputer arbitrairement à A ou à B.
- Un colis vendu à A, transporté par véhicules successifs et remis à C produit une expédition commerciale unique, plusieurs étapes de transport, éventuellement des recettes réparties entre trajets selon contrat, et une seule suite de paiements.
- Une réparation faite dans le garage de B sur un véhicule exploité par A est une opération garage B, un coût analytique véhicule V, une dette/une sortie de caisse selon sa pièce, et potentiellement une dépense propriétaire si son contrat le prévoit.
- Un salarié peut exercer dans plusieurs agences ou véhicules ; son salaire n'est pas imputé intégralement à un véhicule sans politique de ventilation vérifiable.

## Conception UX multi-services

Accueil après connexion = espace du rôle + agence active autorisée + alertes personnelles + barre d'état de synchronisation. Administrateur/Direction : sélecteur entreprise, agence, période et drill-down ; utilisateurs ordinaires : contexte par défaut restreint. Les montants sensibles n'apparaissent qu'aux profils habilités. Afficher toujours états des pièces, statut sync et auteur. Les impressions doivent porter identifiants et provenance. Prévoir ergonomie faible bande passante, équipements de guichet, écrans tactiles et action clavier.

## Résultat d'intégration quotidien

À la fin de la journée, sans ressaisie, la direction obtient : billets vendus et contrôlés ; colis reçus, embarqués, livrés ; voyages réalisés ; heures et kilomètres ; carburant et dépenses garage ; salaires/charges constatés selon période ; avances d'équipage ; caisses attendues/réelles ; soldes partenaires ; résultat analytique par véhicule/voyage ; écritures validées/en attente ; anomalies et agences hors synchronisation. Les dates de disponibilité des données doivent être visibles.
