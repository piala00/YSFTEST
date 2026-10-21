# ERP OHADA — Gestion commerciale · Comptabilité SYSCOHADA · Reporting

ERP conçu pour les PME de l'espace OHADA (FCFA, TVA 19,25 % par défaut — Cameroun). Il comprend :

- un **serveur web Django** (interface navigateur + API REST), compatible **PostgreSQL**, **SQL Server** ou SQLite ;
- un **client bureau CustomTkinter** (Windows / Linux / macOS) qui se connecte au serveur par l'API.

## Architecture : 3 logiciels avec une barre de menus façon Sage 100

Chaque module est un **logiciel à part entière**, avec sa fenêtre, sa couleur et sa propre **barre de menus**,
organisée comme Sage 100c :

```
Fichier · Édition · Structure · Traitement · Etat · Fenêtre · ?
   └─ commandes, séparateurs, sous-menus en cascade ▸
```

Sous la barre de menus se trouvent une **barre d'outils** et une **barre verticale** de navigation (Fenêtre ›
Barre verticale). Le menu **Édition** est actif dans la version web : Couper, Copier, Coller, Effacer,
Sélectionner tout, Ajouter, Voir/Modifier et Rechercher.

**Conformité Sage 100 V12.** Chaque entrée de menu porte un niveau de preuve, selon le skill
`sage-100-gescom-v12-ui` installé dans `.claude/skills/` :
- `DOC-V12` : cité dans le découpage officiel V12.10 ;
- `ERG-CLASSIQUE` : ergonomie Sage classique, à vérifier ;
- `INDICATIF` : proposition non vérifiée ;
- `AJOUT-ERP` : propre à l'ERP OHADA.

La bibliothèque Sage V5–V12 / X3 est aussi installée dans `.claude/skills/` : orchestrateur ERP, Comptabilité,
Gestion commerciale, Objets Métiers, BI Reporting et X3, ainsi que le dictionnaire SQL Sage 100
(`sage100-sql-server-structure-v5-v12`). Ses outils Windows (`resources/outils/`) ne font que lire
(interface, métadonnées SQL, registre COM) : ne jamais les lancer avec un compte qui peut écrire dans une base Sage.

La matrice de traçabilité est générée par `python manage.py audit_navigation --sortie docs/AUDIT_SAGE_V12_GESCOM.md`.
Les points à confirmer sur une installation V12 réelle sont listés dans `docs/SAGE_V12_POINTS_A_VERIFIER.md`.

**Simulateurs à télécharger** (`docs/erp-simulateur-web.html` et `docs/erp-simulateur-bureau.html`). Ce sont deux
fichiers autonomes, sans serveur ni Internet, pour naviguer dans le logiciel comme si l'on y était :
- **version web :** les vrais écrans de l'ERP (546 pages capturées), avec les menus, la barre d'outils et la
  barre de navigation ;
- **version bureau :** le lanceur, la connexion, la barre de menus Windows, l'arborescence, les tableaux, les
  fiches de document, la saisie de facture et l'export CSV.

Les enregistrements sont simulés : rien n'est modifié. Gardez les deux fichiers dans le même dossier pour passer de
l'un à l'autre. Pour les régénérer depuis une base de démonstration : `python manage.py simulateur`.

**Explorateur des menus** (`docs/explorateur-menus-autonome.html`, à ouvrir dans un navigateur). Il reproduit
les barres de menus des trois logiciels. Pour chaque commande, il indique son état dans l'ERP, son niveau de
preuve et l'écran qu'elle ouvre, et permet de la noter « conforme » ou « à corriger », avec un commentaire.
Pour le régénérer après une modification des menus :
`python manage.py explorateur_menus --sortie docs/explorateur-menus-autonome.html --autonome`.

| Logiciel | Barre de menus |
|---|---|
| **Gestion commerciale** | Fichier · Structure · Traitement · État · Fenêtre · ? |
| **Comptabilité OHADA** | Fichier · Structure · Traitement · État · Fenêtre · ? |
| **Reporting** | Fichier · État · Fenêtre · ? |

Exemples :
- *Gestion commerciale › Traitement › Documents des ventes ▸* Devis, Bons de commande, Bons de livraison, Factures, Factures d'avoir, Nouveau ▸
- *Comptabilité › Traitement › Saisie des journaux ▸* un sous-menu par code journal (VT, AC, BQ, CA…)
- *Comptabilité › État › Bilan et compte de résultat ▸* Bilan, Compte de résultat, Soldes intermédiaires de gestion
- *Fichier* : À propos de votre société, Autorisations d'accès, Imprimer, Import/Export, Fermer, Quitter
- *Fenêtre* : ouvre les autres logiciels, chacun dans sa propre fenêtre

Les commandes qui ne sont pas encore développées (Gammes, Dépôts, Rapprochement bancaire, Plan analytique…) apparaissent
**grisées**, comme dans Sage. Sous la barre de menus, une **barre de navigation** à gauche reprend le contenu du menu
choisi sous forme d'arborescence.

Toute la structure est décrite à un seul endroit : `apps/core/navigation.py`. Pour activer une commande grisée,
il suffit de lui associer une page. La même définition alimente :

- **le web** : menus déroulants avec cascades, séparateurs et commandes grisées, ainsi que le portail (`/`) ;
- **le client bureau** : il construit une vraie barre de menus Windows à partir de `/api/navigation/?module=<code>`.

## Modules

### Gestion commerciale (découpage Sage 100 Gestion commerciale V11)

Les menus Fichier, Structure, Traitement et Etat reprennent l'ordre et les libellés du *Découpage fonctionnel détaillé
Sage 100 Gestion commerciale V11*.

**Documents des ventes :** Devis, Bon de commande, Préparation de livraison, Bon de livraison, Bon de retour,
Bon d'avoir financier, Facture, Facture de retour, Facture d'avoir.

**Documents des achats :** Demande d'achat, Préparation de commande, Bon de commande, Bon de livraison, Bon de retour,
Bon d'avoir financier, Facture, Facture de retour, Facture d'avoir.

**Documents des stocks :** Mouvement d'entrée, Mouvement de sortie, Mouvement de transfert (de dépôt à dépôt).

| Règle | Comportement (comme Sage 100) |
|---|---|
| Transformation | Devis → Commande → Préparation → BL → Facture ; BL → Bon de retour → Facture de retour ; Bon d'avoir financier → Facture d'avoir (idem achats) |
| Livraisons partielles | Une commande peut être livrée en plusieurs fois : la colonne « Reste à transformer » suit le reliquat ligne par ligne, et le document reste « Partiellement transformé » jusqu'à reprise complète |
| Stock | Sortie : BL, facture (non issue d'un BL), bon de retour fournisseur, mouvement de sortie. Entrée : BL fournisseur, facture fournisseur (non issue d'un BL), bon de retour client, facture de retour, mouvement d'entrée |
| Avoirs | La facture d'avoir est financière (pas de mouvement de stock) ; la facture de retour remet la marchandise en stock |
| Dépôts | Stock tenu par dépôt (multi-agences) ; chaque document précise son dépôt ; transfert entre dépôts |
| Valorisation | CMUP (coût moyen unitaire pondéré), recalculé à chaque entrée valorisée (achats, mouvements d'entrée) |
| Stock négatif | Refusé par défaut, contrôle par dépôt ; autorisable dans Fichier › Paramètres société › Logistique |
| Inventaire | Traitement › Saisie d'inventaire : état préparatoire, saisie des quantités comptées, puis génération automatique des mouvements d'entrée et de sortie de régularisation |
| Annulation | Un BL validé peut être annulé : le stock est rétabli et le reliquat de la commande d'origine aussi |

Autres fonctions :
- **Catégories tarifaires (GROS, DÉTAIL…) :** le prix proposé dépend de la catégorie du client, et sa source est affichée.
- **Code risque :** si l'encours dépasse le plafond, la pièce est soit validée avec un avertissement, soit bloquée. Le contrôle porte sur les commandes, préparations, BL et factures.
- **Gestion des besoins :** les seuils mini/maxi sont définis par dépôt, et l'ERP propose des bons de commande fournisseur en brouillon.
- **Recherche de documents :** par entêtes ou par lignes, avec filtres domaine, type, statut, dépôt, dates, tiers, n° de pièce et article.
- **Gestion des comptes :** clients et fournisseurs avec solde comptable et reste dû, interrogation des articles.
- **Gestion des livraisons clients et des réceptions fournisseurs :** commandes en attente.
- **Etat** (découpage V12.10, pages 13 et 14) :
  - analyse clients : activité mensuelle, rentabilité au CMUP, risque (encours, échu, dépassement du plafond) ;
  - statistiques clients et fournisseurs par familles et par articles ;
  - palmarès des clients et des ventes ;
  - analyse fournisseurs ;
  - mouvements de stock ;
  - inventaire : état préparatoire et livre d'inventaire ;
  - relevés de factures et d'échéances ;
  - listes des documents, des clients, des fournisseurs et des articles.

  Tous ces états s'impriment et s'exportent en CSV.
- **Règlements :** espèces, chèque, virement, Mobile Money, avec imputation automatique sur les factures.
- **Impression :** tous les documents s'impriment en A4.

### Régime de TVA de la société
Fichier › À propos de votre société › **Régime de TVA** :
- **Assujettie** : TVA facturée aux clients (4431) et TVA des achats déductible (4452) ; stock valorisé HT.
- **Non assujettie** : ventes facturées sans TVA (« TVA non applicable » sur la facture). La TVA payée aux
  fournisseurs n'est pas récupérable : elle entre dans le coût d'achat (charge 60x TTC, CMUP TTC).
- **À paramétrer** (nouvelle société) : traitée comme assujettie, avec un bandeau d'alerte sur toutes les pages
  tant que le régime n'est pas choisi. À l'installation : `python manage.py init_erp --regime-tva non-assujettie`.

Le régime en vigueur s'applique au moment de la validation des documents. Les clients exonérés et les
fournisseurs non assujettis se règlent sur leur fiche tiers (case « Assujetti à la TVA »).

### Reprise d'un dossier Sage 100
`python manage.py reprise_sage --dossier exports --date-bascule AAAA-MM-JJ [--appliquer]` reprend dépôts,
familles, plan comptable, tiers, articles, stock d'ouverture par dépôt et soldes d'ouverture, à partir des CSV
produits par des requêtes **SELECT uniquement** (`--sql`). Simulation par défaut, rapport de rapprochement
(stock, balance), import rejouable. Procédure et correspondance des colonnes : `docs/REPRISE_SAGE100.md`.

### Comptabilité OHADA (SYSCOHADA révisé)
- Plan comptable SYSCOHADA (classes 1 à 9) pré-chargé et modifiable.
- Journaux : Ventes (VT), Achats (AC), Banque (BQ), Caisse (CA), Mobile Money (MM), OD, À-nouveaux (AN).
- **Écritures automatiques** :
  | Opération | Écriture |
  |---|---|
  | Facture client | D 4111 TTC / C 70x HT / C 4431 TVA |
| Facture de retour / facture d'avoir | Écriture inverse de la facture |
  | Facture fournisseur | D 60x HT / D 4452 TVA / C 4011 TTC |
    | Encaissement client | D 52x / 57x / 55x / C 4111 |
  | Paiement fournisseur | D 4011 / C 52x / 57x / 55x |
  | Variation de stock | D 311 / C 6031 (ou inverse) |
- Saisie manuelle d'écritures (brouillard → validation, contrôle d'équilibre), avec section analytique par ligne.
- **Structure** : plan comptable, plan tiers, codes journaux, **taux de taxes** (TVA 19,25 % collectée 4431 /
  déductible 4452), **banques** (RIB, journal de trésorerie), **plan analytique** (sections par plan : agences, activités…).
- **Traitement** :
  - interrogation et lettrage, affichage des lignes lettrées et **délettrage** ;
  - **lettrage automatique** par compte et par tiers : montants identiques, puis reste soldé du tiers ;
  - **rapprochement bancaire manuel** : pointage des opérations sur un relevé, solde comptable, solde banque attendu, écart ;
  - **saisie analytique** : ventilation des charges et produits par section ;
  - **clôture des journaux** : plus aucune saisie ni validation jusqu'à la date choisie ;
  - **clôture de l'exercice** : contrôles (brouillard, exercice précédent), reports à nouveau des classes 1 à 5
    détaillés par tiers dans le journal AN de l'exercice suivant (créé si besoin), résultat en 131 ou 139.
    Les écritures de l'exercice clôturé sont alors remplacées par les à-nouveaux dans la balance, le grand livre et le bilan.
- **Etat** : brouillard, journaux, **grand livre**, **balance générale à 6 colonnes** (les à-nouveaux du journal AN
  vont dans les colonnes d'ouverture), balance âgée, échéanciers, **balance analytique**.
- **Bilan** (actif brut / amortissements / net, passif) et **Compte de résultat** avec les références officielles (TA…, RA…, XA à XI : marge commerciale, valeur ajoutée, EBE, résultat d'exploitation, financier, HAO, résultat net).
- Récapitulatif de la TVA (collectée / déductible / à reverser).
- Exercices comptables : la clôture passe uniquement par Traitement › Fin d'exercice.

### Reporting
- Tableau de bord : CA, marge commerciale, résultat, trésorerie, créances, dettes, stock, graphiques mensuels, top clients et top articles.
- Analyse des ventes par client et par article (avec marge), exports CSV.
- Balance âgée des clients et des fournisseurs (non échu, 1-30, 31-60, 61-90, > 90 jours).

## Installation rapide (développement, SQLite)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py init_erp --demo --admin admin123   # plan comptable + journaux + exercice + données de démo
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000, se connecter avec `admin` / `admin123`, puis choisir un logiciel sur le portail.

Sous Windows, double-cliquer sur `DEMARRER_SERVEUR.bat`.

## Base de données de production

Copier `.env.example` en `.env`, puis choisir le moteur :

- **PostgreSQL** : `DB_ENGINE=postgresql` (ou `docker compose up -d` pour un serveur prêt à l'emploi).
- **SQL Server** : `DB_ENGINE=mssql`, installer `mssql-django` (`pip install mssql-django`) et le pilote *ODBC Driver 18 for SQL Server*.

Ensuite : `python manage.py migrate && python manage.py init_erp --admin <mot_de_passe>`.

## Client bureau (CustomTkinter)

Trois logiciels indépendants et un lanceur :

| Programme | Lancement | Exécutable Windows |
|---|---|---|
| Lanceur (choix du logiciel) | `python lanceur.py` | `ERP_OHADA.exe` |
| Gestion commerciale | `python commercial.py` | `ERP_Commercial.exe` |
| Comptabilité OHADA | `python comptabilite.py` | `ERP_Comptabilite.exe` |
| Reporting | `python reporting.py` | `ERP_Reporting.exe` |

```bash
cd desktop
pip install -r requirements.txt
python lanceur.py
```

Chaque logiciel s'ouvre avec la barre de menus Windows native (Fichier, Structure, Traitement, État,
Fenêtre, ?), un en-tête à sa couleur, la barre de navigation et la zone de travail. Les éléments qui disposent d'un écran natif s'affichent dans la fenêtre :
tableau de bord, tiers, articles, documents de vente et d'achat, saisie de factures et de règlements, balance, bilan,
compte de résultat et balances âgées. Les autres proposent de s'ouvrir dans le navigateur, et un double-clic les
ouvre directement.

Au premier lancement, saisir l'adresse du serveur (ex. `http://192.168.1.10:8000`), l'utilisateur et le mot de passe.
Le jeton est conservé dans `~/.erp_ohada.json` et partagé par les trois logiciels.
Sous Windows : `desktop\DEMARRER_CLIENT.bat`, et `desktop\COMPILER.bat` produit les 4 exécutables dans `dist\`.

## API REST

Authentification : `POST /api/token/` (`username`, `password`), puis en-tête `Authorization: Token <jeton>`.

| Ressource | URL |
|---|---|
| Tiers | `/api/tiers/?type=CLIENT&q=` |
| Articles | `/api/articles/` |
| Documents | `/api/documents/?domaine=ventes&type=FACTURE` · `POST /api/documents/{id}/valider/` · `POST /api/documents/{id}/transformer/` |
| Règlements | `/api/reglements/` |
| Plan comptable, journaux, écritures | `/api/comptes/`, `/api/journaux/`, `/api/ecritures/` |
| Reporting | `/api/reporting/dashboard/`, `balance/`, `bilan/`, `compte-resultat/`, `balance-agee/` (paramètres `du`, `au`) |
| Navigation | `/api/navigation/` (tous les logiciels) ou `/api/navigation/?module=commercial` |

## Tests

```bash
python manage.py test                                # toute la suite
python manage.py test apps.commercial.tests_recette  # cahier de recette SAHEL DISTRIBUTION
python manage.py test apps.comptabilite.tests_recette  # comptabilité et scénarios inter-modules
python manage.py test apps.commercial.tests_tva        # régime de TVA de la société
python manage.py test apps.core.tests_reprise_sage    # reprise d'un dossier Sage 100
```

La **recette Comptabilité** suit le skill `sage100-comptabilite-v5-v12-expert` et les scénarios de la
bibliothèque Sage (`SCENARIOS_INTER_MODULES.md`) : C01 facture transférée sans doublon, C07 paiement partiel
puis lettrage, C08 facture validée non annulable, C10 analytique par agence égale au résultat, plus lettrage
automatique, délettrage, rapprochement bancaire, clôture des journaux et clôture d'exercice (perte ou bénéfice,
bilan d'ouverture égal au bilan de clôture).

Le **cahier de recette** rejoue les cas pratiques du skill `sage-100-gescom-v12-formateur-expert` sur la société
fictive SAHEL DISTRIBUTION : tarification, entrées, transferts, chaîne de vente, livraisons partielles, achats,
inventaire, règlements, encours, retours et avoirs, états, réapprovisionnement. Le détail est dans
`docs/RECETTE_SAHEL_DISTRIBUTION.md`. Pour faire les exercices à la main : `python manage.py init_erp --sahel`.

## Structure

```
erp/                 configuration Django (settings, urls)
apps/core/           société, exercices, numérotation, menus façon Sage (navigation.py), init_erp
apps/commercial/     tiers, articles, documents, règlements, stock
apps/comptabilite/   plan SYSCOHADA, journaux, écritures, états financiers
apps/reporting/      indicateurs et analyses
apps/api/            API REST (Django REST Framework)
templates/, static/  interface web (Bootstrap 5, Chart.js — servis localement, fonctionne hors ligne)
desktop/             logiciels bureau CustomTkinter (shell commun, écrans, lanceur)
```
