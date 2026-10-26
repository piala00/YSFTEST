# Plan de réalisation et tests d'acceptation — à exécuter par Claude

## Ordre des lots

| Lot | Action | Sortie attendue | Validation obligatoire |
|---|---|---|---|
| 0 | Audit dépôt actuel et modèles | matrice existant/manquant, dépendances, migrations, capacités Windows et Web | aucune fonctionnalité supposée construite |
| 1 | Comptabilité de référence / comptes à 7 chiffres | compatibilité numérotation et règles de validation | aucun impact sur écritures existantes, collisions bloquées |
| 2 | Plans multi-axes et allocations | dix plans Transport visibles et Commerce configurable, migration prudente | somme affecté+non affecté par plan=GL |
| 3 | Services analytiques transverses | balance, grand-livre, journal, compte d'exploitation, contrôle | mêmes montants qu'à l'écriture source, droits corrects |
| 4 | Reporting riche + API/UX | catalogue d'états, filtres multi-périodes, drill-down, exports, dashboards | Web/Windows mêmes filtres et chiffres |
| 5 | Simulation opérationnelle | 1–36 mois successifs, sans rupture de chaîne | clôtures mensuelles, soldes reportés, aucune écriture réelle |
| 6 | Simulation prévisionnelle | scénarios à horizon multi-mois, comparatifs et hypothèses | scénarios ne créent aucune écriture générale |
| 7 | Compilation | `ERP_OHADA.exe` utilisable ou installeur/`onedir` complet, option serveur local | tests machine Windows sans Python |
| 8 | Livraison / migration | changelog, tests, build, plan de sauvegarde/rollback | pas de déploiement production sans accord |

## Tests incontournables

**Comptables** :
- Compte `4111` -> `4111000`, numéro déjà long rejeté, collisions `4111`/`4111000` détectées ; aucune mutation avant rapport dry-run.
- Une même charge 1 000 XAF affectée sous deux plans ne devient pas 2 000 XAF au total de la société. Au sein d'un plan, 70 % section A + 20 % B + 10 % non-affecté est conservé sans montant fantôme.
- Résultat d'un véhicule ≠ solde de son propriétaire si avances/règlements différents ; traiter contrats avec dates d'effet.
- Grand-livre analytique d'une section filtré par date/société mène aux lignes d'écritures validées attendues.
- Billetterie VIP imputée à véhicule Classique : anomalie détectée ou rejetée selon règle.
- Petite agence avec une caisse mutualisée : consolidation par agence ≠ somme des « mouvements comptés deux fois » lors des transferts internes.

**Reporting** :
- Toutes les dix rubriques analytiques Transport s'ouvrent, permettent le choix de sections et au moins balance, journal, grand-livre, compte d'exploitation avec périodicité libre.
- Comparatif janvier–mars et avril–juin, période du 1er novembre au 31 janvier de l'année suivante, date isolée, mois sélectionné, N vs N−1, 12 mois glissants ; stabilité des totaux.
- Les montants du Reporting sont **identiques** aux états sources après mêmes filtres. Les tableaux croisent des plans uniquement quand l'allocation multidimensionnelle est prouvable.
- CSV/PDF/XLSX et impression : même périmètre/permissions, totaux cohérents, colonnes non tronquées, date/plan/société visibles.
- Compte sans pièce/traces : cellule signale anomalie, pas silence.
- Compte avec droits restreints : refus côté service/API même si URL saisie directement ou export demandé.

**Simulation opérationnelle** :
- `--mois` historique reste compatible ; deux mois adjacents, six mois, douze mois et traversée décembre/janvier.
- Aucune recréation de société/capital/fournisseurs chaque mois ; paie et propriétaires calculés pour **chaque mois**, pas seulement le dernier.
- Stocks, créances, dettes, trésorerie et contrats subsistent du mois 1 au mois 2 ; aucun doublon lors d'une reprise autorisée.
- Même graine+paramètres+version = résultats identiques en environnement propre ; changements d'hypothèses = résultats documentés.
- Rejet explicite d'une connexion à base réelle même si chemin/base a un nom ressemblant à `simulation` ; opération interdite hors environnement sûr.
- Prise en compte des statuts validés et suppression facile de la base fictive sans incidence production.

**Prévision** :
- Scénarios 3, 6, 12, 24 mois ; variation différenciée carburant, billetterie, créances. Les reports sont cohérents ; aucune ligne écriture enregistrée en production.

**Exécutable** :
- Build propre depuis Windows ; artefact et SHA256 existants et non vides ; tests sur machine sans Python.
- Tous les modules ouvrables via le binaire livré, sans EXE absent ; ouverture des menus et états, export, simulation.
- Test mode serveur distant inaccessible, mode serveur local optionnel, chemins d'écriture après installation et redémarrage.

## Traçabilité attendue

Un tableau d'avancement avec statut `NON COMMENCÉ / EN COURS / FONCTIONNEL TESTÉ / BLOQUÉ / NON APPLICABLE`, chemin, commit, migration, commande test, résultat, preuve. Recommandation de déploiement seulement après tests verts, sauvegarde restaurable et validation utilisateur.
