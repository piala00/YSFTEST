# Architecture cible — un registre général, plusieurs angles analytiques

## Flux et composants

`Événement commercial / transport → validation métier → Écriture générale validée → allocations analytiques multi-plans → moteur d'agrégation unique → états analytiques + reporting + exports`

`Simulation opérationnelle → base SIMULATION isolée → mêmes services métier et mêmes états (bannière données fictives)`

`Prévision scénarisée → tables/namespace de scénarios séparés → moteurs de projections ; jamais Ecriture réelle`

## Modèle cible proposé (à ajuster au code réel)

- **PlanAnalytique** : `id`, `code`, `libelle`, `activites_autorisees`, `societe_id`, `actif`, `ordre`, `favori`, `type_imputation` (directe / ventilée / dérivée), permissions, métadonnées.
- **SectionAnalytique** : plan FK, société/site, `code`, libellé, dates effet, parent facultatif, actif. Préserver l'historique des sections inactives. Unicité recommandée `(societe, plan, code)` et migration contrôlée de l'unicité globale actuelle.
- **AffectationAnalytique** : `ligne_ecriture_id`, `plan_id`, `section_id`, `poids` et/ou `montant`, `methode`, `source` (directe, règle, héritée), auteur, date. **Pas de second Ecriture**. Les ventilations d'une même ligne au sein d'un plan ne doivent pas dépasser 100 % ; le résiduel reste « Non affecté » et n'est pas perdu.
- **RegleVentilation** : priorité, comptes/classes éligibles, agence/service/activité/source, pourcentages et dates d'effet, version et audit ; allocations automatiques **traçables**, avec correction et réexécution contrôlées.
- **EtatDefinition / Colonne / Filtre / Format** : catalogue déclaratif partagé entre Web et Windows, tenant compte de version, rôle, activité et disponibilité des dimensions.
- **ScenarioPrevision** : horizon mensuel, hypothèses, paramètres, version, auteur, état (brouillon, validé, archivé), résultats prévisionnels séparés et lien vers référence comptable figée.
- **SimulationRun** : identifiant, base fictive, période début/fin, graine, hypothèses, état, rapports mensuels, compteurs, contrôles, version du moteur et empreinte des paramètres.

## Mesures communes (API stable)

`revenus`, `charges`, `resultat_exploitation` (avec définition documentée), `encaissements`, `decaissements`, `creances`, `dettes`, `solde_de_tresorerie`, `affecte`, `non_affecte`, `ecart_rapprochement`, `nb_pieces`.

Chaque cellule renvoie au moins : société / période / exercice / plan / section / monnaie / règle de calcul / source des lignes / statut de validation / date d'actualisation. Utiliser `Decimal` sur tous les montants financiers. **La restitution par axe ne change pas le total financier de l'entreprise.**

## Contrôles comptables et allocation

- Sélection par défaut `Ecriture.statut=VALIDEE`, filtrée sur la société autorisée et la date comptable.
- Pour chaque plan `P`, par classe ou nature `C` et période `T` : `GL(P,T,C) = sum(allocations_P(T,C)) + non_affecte_P(T,C)`. L'égalité n'autorise pas à additionner entre plans.
- `balance débit = balance crédit` pour chaque exercice et périmètre documentaire validé, sauf états filtrés volontairement non équilibrés (le signaler clairement).
- Une charge `1000` affectée à 100 % à **Véhicules** et à 100 % à **Agences** reste `1000` en comptabilité générale et dans chaque vue ; **ne jamais l'additionner à `2000`**.
- Frais partagés : clé de ventilation explicite, périodes de validité, justificatif, possibilité de réaffectation versionnée.
- Passage d'un événement d'exploitation vers son écriture générale : lien pièce/source, compatibilité multi-établissements, idempotence des imports/synchronisations.
- Dates : états généraux par **date comptable** ; mesures d'exploitation par **date de l'événement** ; afficher leur base et permettre rapprochement contrôlé sans les confondre.

## Véhicules et propriétaires

- Résultat du véhicule : produits/charges **économiquement affectés au véhicule** selon règles explicites.
- Rémunération du propriétaire : règle contractuelle applicable **à la date pertinente** (forfait, part variable, garantie, avances, commission, etc.).
- Solde financier dû : mouvements tiers/acomptes/paiements/régularisations au compte d'auxiliaire ; **pas égal par défaut au résultat du véhicule**.
- Gammes Classique / VIP : véhicules distincts et dédiés ; l'affectation véhicule→gamme, voyage→gamme doit rester cohérente dans les états.
- Caisses : caisse mutualisée ou multiples par agence ; consolidations éliminent les transferts internes en double selon le type d'indicateur.

## Multi-interfaces et autorisations

Autorisation vérifiée au niveau service et API, pas uniquement à l'affichage des menus ; contrôle société, agence, plan, section, drill-down, export, période, accès prix/coûts, données RH sensibles. Journaliser les exports sensibles. Pagination et agrégations SQL pour grands volumes ; caches avec clés complètes (rôle, société, période, plan, filtres, version calcul) et invalidation lors d'une validation/correction. Ne pas exposer des données d'autres sociétés dans un export.
