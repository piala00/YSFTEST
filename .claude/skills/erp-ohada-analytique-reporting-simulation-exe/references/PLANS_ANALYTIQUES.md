# Plans analytiques — décisions applicables

## Transport : dix plans visibles et consultables

| N° | Plan | Sections typiques (exemples à configurer, non structure imposée) | Analyses incontournables |
|---|---|---|---|
| 1 | Agences / Gares | Bertoua, Douala, Yaoundé… | recettes/dépenses, caisses rattachées, résultat, comparaison agences |
| 2 | Véhicules | immatriculation ou identifiant interne | compte d'exploitation, journal, balance, coûts kilométriques, taux de disponibilité |
| 3 | Propriétaires de véhicules | propriétaire / partenaire | portefeuille, charges/produits affectés, décomptes, solde de compte distinct du résultat |
| 4 | Services / Départements | Billetterie, Courrier, Garage, Administration… | rentabilité par service, frais communs, budgets |
| 5 | Activités | Transport voyageurs, Courrier/colis, Garage, etc. | marge et rentabilité de l'activité |
| 6 | Gammes Classique / VIP | Classique, VIP | contribution, coûts, taux de remplissage, flotte dédiée par gamme |
| 7 | Lignes / Itinéraires | axe et sens de circulation | marge par ligne, coût/km, volumes, comparatifs |
| 8 | Voyages / Départs | voyage/départ identifié | résultat, recette, dépenses, annulations, écart caisse-voyage |
| 9 | Contrats d'exploitation | contrat propriétaire/prestataire | obligations, partage, charges attribuées, solde contractuel |
| 10 | Canaux de vente | guichet, web, application, agence partenaire… | ventes, commissions, coûts de canal, encaissements |

Les **dix** plans sont des rubriques de navigation et des filtres du moteur ; un utilisateur peut ouvrir **un plan**, sélectionner une ou plusieurs sections et générer **compte d'exploitation, balance, grand-livre, journal, charges et produits, comparatifs, anomalies** pour les dates qu'il choisit. Les favoris **Véhicules** et **Propriétaires de véhicules** restent mis en avant dans l'UX mais n'écrasent pas les huit autres. Certains indicateurs non financiers dépendent des données de billetterie/courrier/garage, affichées distinctement des écritures.

### État actuel et trajectoire de migration

Dans l'archive inspectée, `SectionAnalytique.plan` est un `CharField` et `LigneEcriture.section` une seule FK ; `LigneEcriture.vehicule` est une FK distincte. NE PAS perdre ces données. Faire un mapping des anciennes sections vers plans et sections cibles, stocker les allocations et conserver un accès rétrocompatible jusqu'à validation. Le code `apps/transport/reporting.py` expose 5 axes aujourd'hui ; ne pas considérer les 10 plans déjà implémentés.

## Commercial : plans paramétrables par entreprise

Suggestions **non imposées** : `Agences / Magasins`, `Dépôts`, `Commerciaux`, `Clients / Groupes`, `Articles / Familles`, `Activités / Départements`, `Canaux de vente`, `Projets / Contrats`. Chaque société choisit les plans activés et ses sections. Distinguer classification d'article, emplacement stock et imputation de charge : ne pas fabriquer des résultats par plan à partir d'un simple attribut non relié aux écritures validées, sans méthode de ventilation contrôlée.

## Requêtes croisées

Le même écran de Reporting doit autoriser : plan principal, section(s), plan de ventilation complémentaire si la combinaison est sémantiquement valide, classe comptable, exercice, date début/fin, agence, activité, gamme Classique/VIP, véhicule/propriétaire, tiers, produit, utilisateur autorisé.

**Attention** : croisement de deux plans indépendants peut être ambigu si seule une allocation marginale existe par plan. Ne pas produire des intersections monétaires arbitraires en multipliant des parts. Exiger une traçabilité vers les lignes/allocation multidimensionnelle ou indiquer « combinaison indisponible / non attribuable ». Aucune double comptabilisation.
