# 05 — Programme de simulation étendu à plusieurs mois

## Société fictive de référence
- Huit agences au Cameroun (Douala, Yaoundé, Bertoua, Bafoussam, Ngaoundéré, Garoua, Kribi, Ebolowa) ; 300 employés.
- 60 véhicules voyageurs dont **15 appartenant à des propriétaires partenaires**, 45 à la compagnie ; 5 véhicules séparés pour le courrier/fret.
- Répartition de démonstration : 36 Classique et 24 VIP. Capacités adaptées au parc local fictif : VIP le plus souvent 15/20 places et quelques Coasters 30 ; Classique 30/50/55/60/75. Marque et appellation « Saviem » éventuelle comme désignation, **sans assimilation systématique à une capacité**.
- Billetterie, bagages, colis, garages, carburant, péages, achats (demande → devis → bon de commande → réception → facture → comptabilisation → règlement), stocks (pièces, scotch, cartons, papiers), paie mensuelle, allocations et comptes partenaires.
- Caisses : petite gare à caisse commune ; grandes gares et siège à caisses distinctes. Transferts non comptés en CA.

## Commande proposée
`python manage.py simulation_pluri_mois --mois 2026-01 --nombre-mois 12 --echelle 0.1 --rapport docs/retour/SIMULATION_12_MOIS.md --rapport-json docs/retour/SIMULATION_12_MOIS.json`

IMPORTANT : base SQLite isolée dont le nom contient `simulation`, **vide**, migrations préalables. Jamais contre une base réelle. Ne pas permettre `--forcer` dans la commande pluri-mois. Le code joint implémente un enchaînement séquentiel ; tester fonctionnellement sous Django avant de l'utiliser. Les mois complets de 2026 comprennent 28/30/31 jours ; tester aussi le 29 février 2028 et le passage décembre/janvier.

## Modes d'essai
- Smoke : 1 mois et échelle 0,05 ; Recette multi-mois : 3 mois ; Endurance : 6/12 mois ; Continuité : 24/36 mois avec règles de reporting consolidé.
- Même seed, mêmes paramètres → mêmes jeux de données **si la version du moteur et de l'environnement ne change pas**. Enregistrer les paramètres et le hash de version du code ; éviter les heuristiques basées sur l'heure réelle.
- Faire des copies séparées des bases au lieu d'effacer les données d'une première simulation ; pas de réexécution sur une base contenant déjà des voyages.

## Obligations mensuelles
- Produire paie, charges sociales fictives, clôture de caisse, rapprochements banque/MM, valorisation des stocks, états véhicules/propriétaires, échéances fournisseurs, decompte des contrats, balances générales et analytiques, grand livre, compte d'exploitation.
- Générer un **rapport journalier simple par agence** et des états mensuels/société. Mettre `provisoire` tant que synchronisation/comptabilisation est incomplète.
- **Finance, fiscalité et paie** : taux de simulation arbitraires explicitement FICTIFS, à ne jamais réutiliser pour salaire ou taxes réels.

## Contrôles comparatifs et anomalies injectées
Créer scénarios de billet revendu, écart de caisse, bagage non disponible, colis sans véhicule, facture fournisseur non payée, transfert en transit, coupure réseau, ligne GL sans section analytique, partenaire avec salaire fixe + variable, partenaire devenant fournisseur, absence de réseau pendant une semaine, facture antérieure au voyage, immobilisation au lieu de charge, stock négatif interdit.

Émettre deux jeux de résultats : transactions comptabilisées et opérations en attente, avec le détail par mois. Le résultat brut simulé ne prouve pas la conformité fiscale/SYSCOHADA.

**Accès Windows :** le paquet source modifié propose aussi `10-SIMULATION-PLURI-MOIS.bat` au niveau du dossier de lancement. Ce script crée une base dédiée et refuse de réutiliser une simulation déjà présente.
