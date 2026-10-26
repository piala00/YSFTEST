# Reporting cible — général, analytique, exploitation et direction

## Finalité

Créer un **centre de pilotage** qui consomme l'ensemble des services de la comptabilité générale et des dix plans analytiques Transport (ou plans Commerce configurés), pas seulement les quelques tableaux déjà visibles. Les données de ventes/billets, stock, personnel, caisse, kilomètres complètent le pilotage mais ne remplacent pas les montants validés du grand-livre. Chaque rapport doit afficher source des montants, date de référence, droits et horodatage d'actualisation.

## Écran de départ Reporting

- Barre de période universelle : `jour`, `semaine`, `mois choisi`, `trimestre`, `année`, `exercice`, `intervalle libre`, `12 mois glissants`, `cumul exercice`, `N vs N-1`, `budget vs réel`, `scénario vs réel`, `multi-exercices`. Les mois/jours sont sélectionnables **indépendamment** de l'accueil.
- Choix société et établissements autorisés, agence, activité, gamme, plan analytique, sections, comptes à 7 chiffres, pièces, tiers, véhicules, propriétaires, lignes, voyages, contrats, canaux, commerciaux.
- Vues : `Synthèse direction`, `États de comptabilité générale`, `États analytiques`, `Commercial / Transport`, `Trésorerie`, `Rentabilité`, `Budget et prévisions`, `Contrôles / Anomalies`, `Rapports personnalisés`.
- Widgets : chiffre d'affaires, charges, résultat, marge (définir exactement), trésorerie, créances échues, encours, résultat par plan, qualité de ventilation (montants non affectés), variations, alertes et budget consommé.
- Tableau, graphique, comparatif à colonnes, hiérarchie plan→section→pièce, pivot **sans dupliquer** les données, filtre, tri, recherche, favoris, impression.

## Étendue fonctionnelle à fournir

### Comptabilité générale

Balance (générale, soldes, mouvements, auxiliaire), grands livres, journaux/brouillards et validés, états de tiers et âgés, échéancier, soldes bancaires/caisses, rapprochements, compte de résultat, bilan, tableau de flux et notes si *formules et référentiel validés*, variation par comptes, compte d'exploitation, résultat par période, TVA et états déclaratifs configurés. Laisser **non implémenté** ce dont les règles SYSCOHADA/CGI officielles ne sont pas vérifiées ; ne jamais inventer une formule fiscale.

### Analytique

Pour **chaque plan et ses sections** : journal analytique, grand-livre analytique, balance analytique, compte d'exploitation, produits, charges directes/indirectes, charges communes, ventilation et non-affecté, résultat par section, évolution mensuelle, comparaison entre sections et périodes, classement, analyse des écarts, coûts unitaires pertinents, budgets, rapprochement GL/analytique, anomalies, pièces justificatives. Pour Transport ajouter indicateurs métier de véhicules, voyages, propriétaires, gares, gammes, lignes, contrats, canaux, en distinguant mesures d'exploitation et montants comptables.

### Commercial

Ventes, CA net (avoirs et retours correctement déduits), achats, marges selon coût officiel du système, remises, avoirs, stock/inventaire valorisé, rotation et ruptures, clients et groupes, commerciaux, prospection, recouvrement, créances échues/aging, délais de règlement, dépôts/magasins/agences. Conserver les usages existants.

### Transport

Billetterie Classique/VIP, courrier/colis, remplissage, départs, recettes par voyage, rentabilité véhicule, propriétaire/contrat, coûts carburant/maintenance/pneus, mouvements garage, caisses par agence et par service (petite agence : caisse commune possible), modes de règlement, transferts de trésorerie, comparatifs axes/lignes et performance agence ; selon la disponibilité des sources métiers.

## Export et présentation

- PDF imprimable, Excel (`.xlsx`) avec totaux/formules appropriées, CSV UTF-8 séparateur adapté, impression, version tableau et graphique ; les exports respectent les mêmes droits et filtres côté serveur. Fichier exporté : titre, activité, société, période, filtres, mode comptabilisation, devise XAF, horodatage, auteur si autorisé, pagination, totaux, version du calcul.
- Autoriser enregistrement de modèles de rapports personnels/partagés, planification future facultative, comparaison de plusieurs mois avec consolidation ligne par ligne et synthèse.
- Drill-down : KPI → plan → section → compte → écriture → pièce, avec liens aux mouvements source et droits reconfirmés à chaque niveau.
- Valeurs non disponibles indiquées explicitement (`Non calculable`, `Non affecté`, `Donnée manquante`) ; **zéro ≠ absence de donnée**.

## Moteur de calcul commun

API **conceptuelle** à concevoir selon code existant :

```python
# Schéma illustratif, et non API existante à copier telle quelle.
calculer_etat(
    societe=..., periode=(date_debut, date_fin),
    etat='grand_livre_analytique', plan='VEHICULES', sections=[...],
    filtres={...}, base_dates='COMPTABLE', statut='VALIDEE',
    version_calcul='vX', utilisateur=...
)
```

Retour type : `metadata`, `colonnes`, `lignes`, `totaux`, `contrôles`, `source`, `non_affecte`, `version` ; validation des dimensions, provenance, codes des comptes à sept chiffres, pagination. Ne pas fabriquer de résultats pour un croisement sans attribution fiable.

## Critères métier

- Un tableau de **sept mois** et son total = somme des sept états mensuels sur la même base et le même périmètre ; différences dues aux soldes d'ouverture clairement isolées pour les états de situation.
- Une balance globale et la somme affecté + non affecté de chaque plan concordent, sans addition inter-plans.
- Un utilisateur Commercial ne voit pas des données Transport non autorisées et inversement ; le périmètre d'agence doit être appliqué côté serveur, y compris dans les exports.
- Toute demande de période arbitraire doit fonctionner sans défaut `mois actuel` caché dans le code.
- Le modèle `CATALOGUE_ETATS.csv` fixe le backlog avec statut `CIBLE` ; Claude met à jour les statuts d'après l'implémentation vérifiée, **pas** au vu des seuls libellés.
