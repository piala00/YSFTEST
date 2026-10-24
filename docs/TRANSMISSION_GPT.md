# Transmission à GPT : état du projet au 24/10/2026 et suite à décider ensemble

Ce dossier fait le point pour GPT, qui collabore à la conception. Il contient :
- l'état réel du logiciel ;
- la manière de l'exécuter et de le tester soi-même ;
- les scénarios de recette déjà prouvés ou non ;
- les décisions ouvertes ;
- ce que nous demandons pour la suite.

Les faits et le code se vérifient dans le dépôt GitHub `piala00/YSFTEST`, branche `ccr-5592a371-fusjt2`.

## 1. Cadre du projet (inchangé)

- **Objet.** ERP de gestion commerciale, comptabilité SYSCOHADA et reporting pour une société camerounaise. Il prend Sage 100 V12 comme **modèle d'étude** pour l'ergonomie et les fonctions, puis l'adapte.
- **Aucune mention de Sage dans le logiciel visible.** Le nom n'apparaît que dans la documentation d'étude.
- **Fiscalité non imposée.** TVA, NIU, etc. sont paramétrables, rien n'est obligatoire.
- **Bases Sage.** Elles ne sont lues qu'en lecture seule, sans aucune écriture.
- **Données.** Aucune donnée réelle de la société n'apparaît dans les livrables ni sur un site de test public.
- **Organisation métier confirmée par l'utilisateur.**
  - Une seule société, avec plusieurs agences : Bertoua, Garoua-Boulaï, Abong-Mbang…
  - Chaque agence a son propre serveur local, sans interconnexion.
  - Chaque agence gère localement son stock, ses clients et ses créances, et produit ses états mensuels.

## 2. Ce qui est livré dans le logiciel

**Technique** : Django (5.2 ou 6.x), Django REST Framework, SQLite ou PostgreSQL. **155 tests automatisés, tous réussis.**

### Socle

- **Gestion commerciale.**
  - Documents de vente, d'achat et de stock (devis → BC → BL → facture, avoirs, retours, transferts).
  - Stock par dépôt au CMUP, inventaire.
  - Tiers avec payeur, plafond d'encours, code risque et compte bloqué ; règlements.
- **Comptabilité SYSCOHADA.**
  - Journaux, comptes, écritures, lettrage, rapprochement bancaire, analytique, clôtures.
  - Comptabilisation automatique des pièces et contrôle de liaison gestion ↔ comptabilité.
- **États.** Balance, grand-livre, balance âgée, justificatif de solde, statistiques. Chaque état passe par une fenêtre de sélection.
- **Interface de type bureau.**
  - Fenêtres internes déplaçables, redimensionnables et réductibles, qui peuvent s'afficher côte à côte.
  - Barre verticale en accordéon, listes avec filtres et tri, fenêtre de pièce.
- **Administration.**
  - Droits par menu et journal des événements (qui, quoi, quand).
  - Sauvegarde et restauration, fichiers liés.
  - Reprise d'un dossier Sage par export SQL en lecture seule.

### Tranche « agences, caisse, stock, crédit » : réponse au skill `erp-ohada-agences-hors-ligne-rapport-stock`

La matrice complète des exigences E01–E44 et P01–P26 (existant, écart, preuve) est dans `docs/MATRICE_AGENCES_CAISSE_STOCK.md`. En résumé :

| Sujet | Ce qui fonctionne |
|---|---|
| Agences | Agence locale et autres agences ; compte de liaison 185NN créé automatiquement et modifiable |
| Opérations de caisse | Dépense, **versement hors recettes** pour une autre agence (caisse / liaison), **sortie pour le compte d'une autre agence**, autres entrées et sorties ; toutes comptabilisées |
| Avances sur bon de commande | Reçu lié au BC, imputé automatiquement sur la facture issue de la commande à sa validation, sans double encaissement |
| Rapport commercial journalier | 1) ventes (factures comptant, payées d'avance, en compte ; bons de commande) ; 2) encaissements, hors recettes, versements de nos clients reçus par d'autres agences ; 3) sorties et dépenses ; 4) solde de caisse rapproché du compte de trésorerie |
| Versement d'un client dans une autre agence | Agence qui encaisse : opération « hors recettes ». Agence propriétaire de la créance : reçu avec l'agence qui a encaissé et le n° de son reçu (unique), passé sur la liaison sans toucher la caisse locale, facture soldée |
| Reçu de règlement | **Obligatoirement rattaché à une facture** validée du client (ou de son payeur), montant ≤ reste dû ; l'avance sur BC reste un circuit distinct |
| Client au comptant ou à crédit | Case « Client à crédit » sur la fiche. Un client au comptant est signalé à la saisie et au rapport, sans blocage |
| Auteurs | « Créé par » enregistré côté serveur sur pièces, reçus, écritures, opérations de caisse, inventaires et pointages ; « validé par / le » et « annulé par / le » sur les pièces ; bandeau visible à l'ouverture |
| Fiche de stock du fichiste | Saisie du n° du bon ; articles chargés **sans quantité** ; le fichiste saisit les quantités du bon papier ; conforme ou écart immédiat. Les quantités de l'ordinateur sont réservées aux contrôleurs. Aucune sortie de stock en double. Une correction exige un motif et l'historique est conservé. Rapprochement fiche / ordinateur par article |

## 3. Tester soi-même le logiciel

### A. Sans rien installer : les simulateurs (dossier `simulateurs/` du zip)

- **`erp-simulateur-bureau.html`** : le bureau avec les fenêtres internes.
- **`erp-simulateur-web.html`** : 600 écrans du vrai logiciel, avec les données de démonstration.
- **`explorateur-menus.html`** : tous les menus et commandes.

Ce sont des simulations : les saisies ne sont pas enregistrées. Gardez les fichiers dans le même dossier.

### B. Exécuter le vrai logiciel (environnement Python 3.10 ou plus, sans Internet)

Le zip contient le code source (`source/`) et les paquets nécessaires (`paquets/`).

```bash
cd source
pip install --no-index --find-links ../paquets "Django>=5.2,<5.3" djangorestframework whitenoise
python manage.py test                       # 155 tests attendus, tous OK
python manage.py migrate
python manage.py init_erp --demo --regime-tva automatique
python manage.py createsuperuser            # choisir son propre mot de passe
python manage.py runserver                  # puis http://127.0.0.1:8000
```

Si le navigateur n'est pas disponible, on peut tester par le shell Django (`python manage.py shell`) ou par l'API REST (`/api/`). Les tests sont de bons exemples d'utilisation :
- `apps/reporting/tests_rapport_commercial.py` ;
- `apps/commercial/tests_fiche_stock.py` ;
- `apps/commercial/tests_payeur.py`.

### C. Version en ligne de l'utilisateur

L'utilisateur héberge une version de test sur PythonAnywhere (mise à jour par `deploy/pythonanywhere_mettre_a_jour.sh`). Il vous en donnera l'adresse s'il le souhaite. L'aperçu GitHub Pages n'est pas publié : la publication n'est pas encore activée par le propriétaire du dépôt.

## 4. Scénarios de recette du skill (R01–R38) : où en est-on ?

**Statuts :**
- **Prouvé** : couvert par un test automatisé.
- **Manuel** : faisable dans le logiciel mais pas encore testé automatiquement.
- **Non livré** : la fonction n'existe pas encore.
- **Décision** : en attente d'un arbitrage.

| Id | Sujet | Statut | Remarque |
|---|---|---|---|
| R01 | Deux sociétés | Non livré | Aujourd'hui, une base par société (isolation physique) |
| R02 | Agence sans Internet | Manuel | Serveur local, aucun service distant requis ; installation Windows à empaqueter |
| R03, R05, R24, R25 | Synchronisation, fraîcheur, transit, reprise | Non livré | Prochaine grande tranche (consolidation) |
| R04 | Client de Bertoua verse 100 000 à Garoua-Boulaï | Prouvé | Hors recettes d'un côté, reçu « encaissé par une autre agence » de l'autre ; doublon de reçu refusé |
| R06 | Versement pour une facture distante inconnue | Décision | D19 |
| R07 | Agence A paie 20 000 pour B | Prouvé | Sortie pour une autre agence |
| R08 | Rapport complet et solde | Prouvé | |
| R09 | Mobile Money sans entrée d'espèces | Manuel | Le mode existe ; le rapport suit la caisse choisie (journal). Un rapport multi-modes reste à préciser |
| R10, R38 | Avance J1, livraison et facture J2 | Prouvé | |
| R11 | BC livré le jour → facture automatique | Décision | D06 : quel événement prouve la livraison |
| R12 | BL imprimé sans livraison | Prouvé par conception | L'impression ne valide rien |
| R13 | Livraison partielle | Manuel | Transformation partielle possible ; politique de facturation : D07 |
| R14 | Le fichiste ne peut pas déduire l'attendu | Prouvé (écran) | **Reste à vérifier** : API REST et exports accessibles au fichiste ; droits à restreindre |
| R15, R16 | Pointage conforme ou écart | Prouvé | |
| R17 | Ligne vide ≠ zéro déclaré | **Écart** | Une ligne vide vaut aujourd'hui 0 : à corriger |
| R18 | BL non pointé après délai | Partiel | Liste des « bons à pointer » ; pas encore d'alerte de délai |
| R19 | BL modifié après pointage | Prouvé par conception | Un BL validé n'est pas modifiable ; versions de BL non gérées |
| R20–R22 | Cartons et litres, fractionnement, historique des facteurs | Non livré | Tranche « conditionnements » |
| R23 | Concordance BL ≠ inventaire physique | Prouvé par conception | Inventaire séparé du pointage |
| R26 | Opération tardive après clôture | Manuel | Clôture de caisse journalière non figée |
| R27 | Activer le détail après démarrage | Non livré | Assistant de paramétrage |
| R28 | Réutiliser un module existant | Appliqué | Voir la matrice |
| R29 | Reçu sans facture | Prouvé | |
| R30 | Paiement partiel 100 000 puis 50 000 | Prouvé | Plusieurs reçus sur une même facture |
| R31 | Un versement pour deux factures | Décision | D16 ; aujourd'hui, un reçu par facture |
| R32 | Reçu sur une facture soldée ou d'un autre client | Prouvé | |
| R33 | Échéance historique conservée | Prouvé par conception | L'échéance est stockée sur la facture |
| R34 | Plafond global entre agences | Décision | D18 ; pas de garantie stricte hors ligne |
| R35 | Auteur visible à l'ouverture | Prouvé | |
| R36, R37 | Auteur d'origine après synchronisation ; automate | Partiel | Une pièce automatique ou reprise affiche « auteur inconnu (reprise ou traitement automatique) » ; la synchronisation n'est pas livrée |

## 5. Questions ouvertes pour l'utilisateur

Ces questions reprennent D01–D20 du skill ; elles demandent l'avis de GPT puis le choix de l'utilisateur.

1. **D06 / R11.** Pour facturer automatiquement un BC livré le jour même, quel événement prouve la livraison : la validation du BL, ou une confirmation du magasinier ?
2. **D04.** Dans le rapport, « en compte » et « à crédit » sont-ils synonymes ? Quelles colonnes exactes attend l'utilisateur ?
3. **E35.** Un client au comptant dont la facture n'est pas réglée doit-il être bloqué, ou seulement signalé ?
4. **D16 / R31.** Un versement unique pour plusieurs factures : un reçu par facture (actuel), ou un versement réparti sur plusieurs factures ?
5. **D01, D14.** Conditionnements :
   - liste réelle des présentations (carton de 15 L, bidon de 5 L, litre, sac de 50 kg…) ;
   - vente au vrac ou emballages séparés ;
   - prix par présentation.
6. **D03, D09, D13.** Consolidation : quel canal de transmission entre agences (clé USB, courriel, Internet intermittent), à quelle fréquence, avec quelle identification commune des clients ?

## 6. Proposition de suite (à discuter)

**Ordre proposé par Claude :**
1. **Corrections rapides.**
   - R17 : distinguer « non saisi » de « 0 déclaré ».
   - R14 : interdire au profil fichiste l'API et les exports qui révèlent les quantités.
   - R18 : alerte de bon non pointé après un délai paramétrable.
2. **Conditionnements (gros et détail, E09–E11, P07–P08).**
   - Unité de base par article et présentations avec facteur et prix.
   - Facteur conservé sur chaque ligne de pièce.
   - Stock tenu dans l'unité de base.
   - Pas de conversion kg ↔ litre automatique.
3. **Assistant de paramétrage de la société (E12)** : gros, détail, agences, TVA, dépôts, caisses.
4. **Consolidation des agences (E08, P01–P06, P20–P21).**
   - Export signé des opérations de chaque agence et import central sans doublons.
   - Date de fraîcheur affichée par agence.
   - Vue regroupée des stocks, créances et analyses.
5. **Facturation automatique du BC livré le jour (R11)** dès que D06 est tranchée.

## 7. Ce que nous demandons à GPT

1. **Tester le logiciel** (section 3), en particulier les scénarios marqués « Manuel », « Partiel » ou « Écart ». Rendre un fichier `ANOMALIES.csv` (UTF-8, séparateur `;`) avec les colonnes : `id;scenario;etapes;resultat_attendu;resultat_obtenu;gravite(bloquant|majeur|mineur);fichier_ou_ecran`.
2. **Donner son avis sur l'ordre de la section 6** et sur les questions de la section 5. Il s'agit de propositions argumentées : le choix final revient à l'utilisateur.
3. **Recherche documentée sur les conditionnements dans Sage 100 V12**, modèle d'étude, pour préparer la tranche 2. Sujets :
   - conditionnements et unités de vente (fiche article, onglets, champs, libellés exacts) ;
   - gammes, prix par conditionnement et catégorie tarifaire ;
   - saisie dans les pièces, effet sur le stock et sur les états ;
   - versions concernées.

   Rappel des règles : citer la source et la version, séparer le fait, la déduction et l'inconnue, ne rien inventer.
4. **Spécification de consolidation des agences** (tranche 4) pour une société dont les agences travaillent hors ligne :
   - format d'échange, identifiants stables, rejeu sans doublons, accusés de réception ;
   - correspondance des clients et des comptes de liaison entre agences ;
   - ce qui doit rester local et ce qui se regroupe.

**Format de livraison** : comme les précédentes, un skill zippé (`SKILL.md` + `references/*.csv` ou `*.md`, UTF-8), plus `ANOMALIES.csv` pour les tests. Les points de `docs/DEMANDE_GPT_PROCHAINE.md` non couverts par la livraison du 22/10 restent valables, mais passent après ceux-ci.

## 8. Fichiers utiles dans le dépôt

| Fichier | Contenu |
|---|---|
| `docs/MATRICE_AGENCES_CAISSE_STOCK.md` | Exigences E/P : existant, écart, preuve |
| `docs/FEUILLE_DE_ROUTE.md` | Feuille de route générale |
| `docs/HEBERGEMENT_PYTHONANYWHERE.md` | Hébergement de test |
| `.claude/skills/` | Tous les skills livrés par GPT et intégrés |
| `apps/commercial/models.py` | Pièces, règlements, caisse, pointage |
| `apps/reporting/services.py` (`rapport_commercial`) | Calcul du rapport journalier |
| `apps/commercial/fiche_stock.py` | Fiche de stock et rapprochement |
