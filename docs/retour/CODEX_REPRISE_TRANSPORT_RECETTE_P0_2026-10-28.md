# Reprise Codex — Reporting Transport, recette P0 et audit des commandes

Date : 28 octobre 2026. Auteur : Codex.
Référence figée : `f9bb3b26223261c43f5f296a2c7f62665bb37413`, branche `ccr-5592a371-fusjt2`.
Coordination : issue #1 ; audit antérieur : PR #8.
**Livraison documentaire de reprise, pas une livraison fonctionnelle ni une recette complète.**

## Travail existant conservé

L'issue #1 distingue désormais Commerce et Transport et ordonne les lots 03 (Reporting),
04 (tests P0), 05 (commandes sans action). Les anciens messages proposant l'export Excel
ne constituent plus la priorité de cette reprise. Le reporting comparatif utilise déjà
`plan_analytique.faits` ; il faut le réutiliser, pas créer un second moteur monétaire.

La PR #8 est ouverte et en brouillon, tête `856040ea70491af6209b3c0e86ec1f01df10e779`.
Son contenu a été consulté par le patch GitHub. GitHub retourne `mergeable=false` lors
de la reprise : intégration à diagnostiquer, pas de fusion ni de réécriture d'historique.
Ce retour ne prouve pas à lui seul la nature des conflits. Les dix constats antérieurs
restent des constats statiques ; cette note ne les recompte pas comme défauts exécutés.

## Constats nouveaux vérifiés dans les sources

### TR-01 — Montant des colis hors source comptable validée (P1)

Dans `apps/transport/reporting.py:192`, `tableau_de_bord.resume` calcule
`colis_recette` avec `sum(c.prix or ZERO for c in colis)`.
Le queryset sélectionne la date d'enregistrement et exclut les colis annulés,
sans sélectionner une écriture validée. Le résultat est affiché sous le libellé
« Recette colis et fret ». Les produits/charges du même tableau utilisent au contraire
`_periode`, qui lit `pa.faits` à la ligne 58.

Il s'agit d'un **écart de source prouvé dans le code** à la règle du lot 03,
pas d'une corruption du grand livre démontrée. Un colis enregistré mais sans
écriture validée contribue à cette somme ; la démonstration avec base reste à exécuter.

Les fonctions `activite_billetterie` (ligne 113) et `activite_colis` (ligne 142)
additionnent aussi les prix métier. Leurs docstrings décrivent une vue d'exploitation :
ne pas supprimer ces informations sans distinguer exploitation, produits validés et encaissements.

Correction proposée : conserver nombres/poids/statuts comme mesures d'exploitation ;
calculer les montants financiers via les faits validés, en documentant service, date
comptable et non-affecté. Ni prix du billet ni valeur d'un colis ne prouvent un encaissement.
Régression attendue : colis non comptabilisé, écriture brouillon, écriture validée,
annulation/extourne et comptabilisation à une autre date ; aucune double recette.

### TR-02 — Export CSV du tableau de bord non traité dans la vue (P2)

`apps/reporting/views_analyses.py::transport_tableau_de_bord` rend directement le template.
Il n'a pas de traitement `export=csv`, contrairement à `transport_billetterie` et
`transport_colis`. La route existe dans `apps/reporting/urls.py`.
Inspection seulement : aucun clic navigateur exécuté. Ajouter le CSV dans le même
chemin authentifié, avec période et périmètre identiques ; tester le contenu, pas seulement HTTP 200.

### AU-01 — Matrice globale toujours vide (P1, persistance d'un constat antérieur)

`docs/retour/MATRICE_AUDIT_GLOBAL_ERP_SAGE.csv` contient uniquement son en-tête :
zéro ligne de données au commit examiné. Ce n'est pas une nouvelle anomalie à ajouter
aux dix constats de la PR #8. Les matrices commerciales distinctes ne sont pas niées.
Aucun taux de couverture globale ni conformité Sage ne peut être annoncé.

## Lots fonctionnels proposés, PR séparées

| Lot | Périmètre et source | Réception minimale |
|---|---|---|
| 03A | TR-01 et séparation des indicateurs financiers/exploitation | faits validés uniquement ; brouillons exclus ; rapprochement et CSV |
| 03B | remplissage par départ/heure et colis non livrés depuis N jours | compteurs d'exploitation ; capacité nulle sans division ; annulés exclus ; seuil/date de référence documentés ; graphique dans Reporting et CSV |
| 03C | retards/incidents puis coût/km et recettes équipage | vérifier disponibilité/historique des heures, kilomètres et affectations ; aucune estimation présentée comme donnée réelle |
| 04 | recette P0 des actions de la PR #8 | droits, clôtures, équilibre, double soumission et absence d'effet partiel |
| 05 | menus inactifs et matrice exhaustive | cible existante, implémentation ou hors périmètre explicite ; aucune conformité sans preuve Sage |

Les propositions 03B/03C ne sont pas présentées comme des fonctions absentes partout :
l'inventaire complet reste à faire avant d'ajouter un écran. Les graphiques demandés
dans Reporting ne doivent pas être ajoutés au rapport journalier d'agence, dont le
skill impose des tableaux simples.

## Recette critique à exécuter (non exécutée ici)

- `ecriture_valider`, `ecriture_supprimer`, `cloture_exercice` :
  refus de mutation en GET ; profil interdit → 403 ; période clôturée ;
  soumission répétée ; écritures équilibrées ; transaction sans effet partiel.
- `billet_vente`, `cloture_journee` :
  mêmes contrôles, plus caisse/agence/service, absence de double billet ou encaissement,
  rapprochement espèces distinct de Mobile Money et ventes à crédit.
- `document_valider`, `transformer`, `annuler` :
  mêmes contrôles, plus stock, règlement, pièce source, traces auteur et extourne.
- **Distinguer formulaire et mutation** : une vue de vente ou de clôture peut
  légitimement afficher son formulaire en GET. Exiger l'absence de mutation en GET ;
  exiger 405 sur une route d'action POST uniquement. Ne pas imposer 405 à tous les formulaires.
- Chaque scénario compare l'état avant/après (pièces, lignes, soldes, stock, traces),
  y compris en échec. Une simple réponse HTTP ne prouve pas l'intégrité.

## Audit exhaustif : suite sans déclarer une exhaustivité acquise

Réutiliser `.claude/skills/audit-exhaustif-erp-sage/SKILL.md` et la matrice existante :
commande → JS → route/méthode → droit → service/transaction → effets métier → preuve.
Priorité aux actions P0 puis aux commandes sans cible. Inclure ensuite installation,
administration du poste et licence signalées par Claude. Distinguer
`A_TESTER_ERP`, `A_VERIFIER_SAGE`, `SPECIFIQUE_ERP` et `INACTIF_VOLONTAIRE`.
Aucune installation Sage V12 consultée dans cette reprise.

## Vérifications réellement réalisées et blocages

- Consultation par l'intégration GitHub de l'issue #1, métadonnées/patch de la PR #8,
  consignes AGENTS.md et sources citées à la référence figée.
- Analyse AST Python de quatre fichiers récupérés : `reporting.py`,
  `views_analyses.py`, `urls.py`, `plan_analytique.py` : syntaxe acceptée.
- Lecture CSV de la matrice globale : zéro donnée.
- GitHub Actions observées sur le commit de référence :
  [Contrôle 40667317437](https://github.com/piala00/YSFTEST/actions/runs/40667317437)
  et [Aperçu 40667317227](https://github.com/piala00/YSFTEST/actions/runs/40667317227)
  terminées avec conclusion `success`. Ce sont des exécutions préexistantes,
  pas des tests lancés par Codex ni une validation de cette PR.
- **Non exécutés** : suite Django, tests P0, SQL Server, navigateur, compilation Windows.
  Le proxy local `proxy:8080` refuse la connexion et Django n'est pas installé.
  La demande d'accès réseau précédente n'a pas abouti.
- Le dossier de transmission annoncé comme joint n'est pas accessible dans la conversation
  ni les répertoires de fichiers disponibles. Ne pas déclarer sa lecture intégrale faite.

La consigne AGENTS.md exige la suite Django avant de pousser. Elle n'est pas satisfaite :
ce brouillon documentaire sert explicitement à transmettre les constats demandés ;
il ne doit pas être validé comme livraison et reste bloqué avant toute intégration.
Aucun code applicatif modifié, aucune migration, aucune donnée de production touchée.

## Décisions ou éléments nécessaires

1. Fournir le dossier de transmission manquant pour vérifier les priorités définitives.
2. Rétablir un environnement d'exécution du dépôt pour les tests complets avant toute livraison fonctionnelle.
3. Revue contradictoire de TR-01 : confirmer la séparation attendue entre valeur opérationnelle,
   produits validés et encaissements, sans relâcher la source comptable unique.
4. L'autorisation de fusion appartient au propriétaire ; la proposition de Claude
   de fusionner les PR vertes ne vaut pas autorisation dans cette reprise.
