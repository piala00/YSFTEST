# Simulation avancée — deux usages distincts

## A. Simulation opérationnelle (jeu de données fictif, plusieurs mois)

### Diagnostic d'origine

`apps/transport/management/commands/simulation.py` utilise `--mois YYYY-MM`, crée la liste des jours d'un unique mois puis appelle `fin_de_mois()` une fois. Le BAT `deploy/windows/7-SIMULATION.bat` force septembre 2026. Il faut **étendre ce programme existant**, pas en écrire un autre qui fabrique des écritures arbitraires en contournant les services métier.

### Interface cible

Exemples **de commandes à implémenter, non encore présentes dans le logiciel** :

```bash
python manage.py simulation --debut-mois 2026-01 --nombre-mois 12 --graine 2026 --rapport-dir rapports/simulation_2026/
python manage.py simulation --debut-mois 2026-10 --fin-mois 2027-03 --graine 2026 --echelle 0.2
# Compatibilité :
python manage.py simulation --mois 2026-09
```

Paramètres validés : premier mois, dernier mois OU nombre de mois (saisie non contradictoire), échelle, graine, taille de flotte/effectif fictif, saisonnalité, scénarios métier, option de reprise contrôlée, dossier de sortie ; maximum configurable (cible initiale 1 à 36 mois), estimation de charge, progression par jour et mois.

### Algorithme de référence

1. Refuser toute base non **explicitement déclarée comme simulation** (flag applicatif + identité de base + absence de société réelle), plus contrôle robuste des accès. Ne jamais permettre `--forcer` dangereux depuis le menu de production.
2. Créer les référentiels fictifs (société, collaborateurs, 8 gares, véhicules VIP/Classique dédiés, contrats, articles, journaux, comptes à sept chiffres) **une seule fois** au démarrage, dans base isolée.
3. Pour chacun des mois consécutifs, avec gestion des années bissextiles et changements d'exercice :
   - parcourir tous les jours chronologiquement avec date d'exploitation et date comptable cohérentes ;
   - générer des opérations par les **services métiers réels** (billets, colis, voyages, carburant, garage, achats, paie, règlements, caisses, propriétaires, règlements tiers, réapprovisionnement…), selon paramètres fictifs ;
   - conserver la trésorerie, stock, créances, dettes, contrats et kilométrages d'un mois à l'autre ;
   - à la fin de **chaque mois**, générer la paie, les décomptes partenaires, les règlements et les calculs prévus, **sans recréer** le capital ni les référentiels ; les écritures doivent être idempotentes à la reprise ;
   - produire bilan général et analytique par chacun des plans disponibles, indicateurs transport et rapports de contrôle ; enregistrer un checkpoint vérifiable, commit par lot raisonnable.
4. À la fin : `01_Janvier.md`… / rapport récapitulatif par mois / comparatif cumulé / courbes / écarts / contrôles ; enregistrer la graine et paramètres pour reproductibilité.
5. Détecter les trous de dates, doublons de clôture, périodes clôturées, régularisations d'exercice, investissements/amortissements si référentiels paramétrés ; **ne pas simuler des taux fiscaux légaux imaginés**. Les éléments non couverts doivent être reportés en limites visibles.

### Données fictives réalistes

Options variables mensuelles : saisonnalité des voyages, pic fêtes, inflation carburant, variation tarifs, accidents/maintenance, pannes, baisse fréquentation, billets annulés/remboursés, inflation des charges, charges de siège, dépôts, recouvrement différé, période de basse saison, variation de taux de remplissage, contrats début/fin, propriétaires ; documenter ce qui a réellement été simulé.

### Conservation/volumétrie

À échelle 1, un mois observé dans l'ancien document de simulation affichait plus de 53 000 écritures ; 12 mois à charge analogue peuvent dépasser 600 000 opérations. Prévoir progression, pagination, commits maîtrisés, index, limite mémoire, mode rapide `--echelle`, et reprises à checkpoints. **Ne promettre aucune durée d'exécution**. Tester avec 2, 3, 12 mois sur machine adaptée et séparer fonctionnalités métier/performances.

### Rapports et contrôles mensuels

`débits = crédits`, `affecté+non_affecté=montant général` par plan, cohérence caisse et transferts internes, solde de banque, stocks comptables vs magasin, décompte propriétaire vs compte de tiers, paie et mois exact, détection des doublons, dette fournisseur, cohérence VIP/Classique. Réaliser comparatif mois par mois et cumuls.

## B. Simulation prospective (budgets et what-if ; sans écritures de production)

### Fonction

Un utilisateur autorisé choisit 1 à 36 mois (extension configurable), base historique réelle **en lecture seule**, hypothèses par mois, saisonnalité, année de départ, scenarios `Base`, `Optimiste`, `Prudent`, `Personnalisé` avec versions. Ne pas transformer automatiquement une simulation en écritures générales. Toute comptabilisation réelle ultérieure suit workflow métier distinct et confirmation.

### Variables

Transport : fréquentation, remplissage, prix billet Classique/VIP, itinéraire, flotte disponible, km, carburant, maintenance, part partenaires et formule contractuelle, frais généraux, commissions, encaissement différé, courrier/colis, caisse, masse salariale. Commerce : prix, quantités, familles, ruptures, CMUP/coût d'achat, marges, recouvrement, délais fournisseurs, stock mini/maxi, charges et investissements.

### Sorties

Tableau par mois, cumul, scénario comparé au réel, tableaux généraux prévisionnels clairement **non officiels**, résultat analytique par plan, trésorerie projetée, besoin de financement, seuil de rentabilité, charges, risques et hypothèses explicites, exports PDF/XLSX/CSV et graphiques. Règles de taux/TVA/impôts sous réserve de paramétrage validé.

### Risques spécifiques

Ne pas confondre simulation fictive d'opérations et projections ; protéger les données réelles. Garder les comptes 7 chiffres et n'afficher des chiffres comptables simulés que si l'algorithme de projection justifie leurs liens et contrôles. Toute hypothèse estimée doit être étiquetée comme telle. Limiter les accès aux hypothèses de paie et données sensibles.
