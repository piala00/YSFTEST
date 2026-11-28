# 01 — Architecture fonctionnelle et navigation

## Séparation des deux modules

La comptabilité générale produit le **référentiel légal et fiscal de l'entité juridique** ; la comptabilité analytique produit une **lecture de gestion concentrée sur les véhicules et propriétaires**. Deux interfaces et deux ensembles de requêtes ; utiliser des entités sources communes et **ne pas maintenir deux vérités financières indépendantes**.

**Comptabilité générale** : accueil/indicateurs société, plan général SYSCOHADA configurable, tiers et journaux, pièces à comptabiliser, écritures brouillon/validées, règlements & lettrage, rapprochements, banque/caisses, balance, grand livre, bilan, compte de résultat, clôture. Les données provenant de toutes les agences remontent au siège ; la vue par établissement peut rester filtre du module général.

**Comptabilité analytique** : `Véhicules`, `Propriétaires`. Chaque écran offre des sous-onglets adaptés : synthèse, mouvements de recettes, dépenses/charges, voyages, historique, règlements applicables et justificatifs. Sélection par période, véhicule/immatriculation, propriétaire, gamme, agence d'exploitation, agence de vente, ligne, voyage, statut synchro. La fiche propriétaire liste tous ses véhicules et laisse ouvrir une fiche véhicule filtrée par période de détention.

## Paramètres internes, non nouvelles rubriques de reporting

Préserver les dimensions déjà retenues (AGC agences, VEH véhicules, PRT propriétaires, DEP services, ACT activités, GAM Classique/VIP, LIG lignes, VOY voyages, CTR contrats, CAN canaux). Les menus "Plans analytiques", "Sections", "Clés de répartition", "Validation des ventilations" deviennent des **paramètres avancés** de Gestion comptable, accessibles au comptable/administrateur, ou restent dans la configuration si existants. Ne pas recréer les 10 pages principales d'analyses.

## Gestion des véhicules

- Clé stable par véhicule (`vehicle_id`), code et immatriculation, modèle, capacité, flotte/gamme avec historisation et périodes sans chevauchement.
- Classification Classique / VIP exclusive par date ; les départs passagers respectent cette gamme. Tout changement exceptionnel est tracé et validé.
- Propriétaire = société exploitante ou partenaire externe selon l'intervalle contractuel ; historisation des droits d'exploitation.
- Propriétaire possédant N véhicules = N comptes d'exploitation + 1 restitution portefeuille, **sans produire N fois une recette générale**.
- Un véhicule peut générer du transport de colis ; conserver `activité = colis` même pour bus VIP.

## Unité d'analyse et périodicité

- Événement de vente/encaissement: date vente, date encaissement, agence de vente.
- Prestation de transport: date voyage/réalisation, véhicule effectif et agence exploitation.
- Dépense: date service/consommation ou période de rattachement, justificatif, lieu de paiement éventuellement différent.
- Rapport par véhicule/partenaire peut présenter plusieurs bases (activité, engagement, encaissement) mais **ne jamais additionner des agrégats de bases différentes** ; titres explicites et règles validées.

## Expérience utilisateur

Rapports en **tableaux simples**, montants FCFA lisibles, totaux et sous-totaux clairs, en-tête compagnie/agence/période, date de dernier synchronisation, statut provisoire, liens vers justificatifs, boutons imprimer/PDF/Excel selon fonctionnalités existantes. Éviter graphiques décoratifs qui remplacent l'information comptable. Pas de saisie obligatoire des plans par guichetier ou mécanicien.
