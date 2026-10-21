# ERP OHADA — Gestion commerciale · Comptabilité SYSCOHADA · Reporting

ERP conçu pour les PME de l'espace OHADA (FCFA, TVA 19,25 % par défaut — Cameroun). Il comprend :

- un **serveur web Django** (interface navigateur + API REST), compatible **PostgreSQL**, **SQL Server** ou SQLite ;
- un **client bureau CustomTkinter** (Windows / Linux / macOS) qui se connecte au serveur par l'API.

## Architecture : 3 logiciels avec une barre de menus façon Sage 100c

Chaque module est un **logiciel à part entière**, avec sa fenêtre, sa couleur et sa propre **barre de menus**,
organisée comme Sage 100c :

```
Fichier · Structure · Traitement · État · Fenêtre · ?
   └─ commandes, séparateurs, sous-menus en cascade ▸
```

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

### Gestion commerciale
- **Tiers** : clients et fournisseurs (NIU, RCCM, délai de paiement, plafond d'encours, assujettissement TVA).
- **Articles** : marchandises / produits finis / services, familles, prix d'achat et de vente, TVA, stock d'alerte.
- **Cycle des ventes** : Devis → Bon de commande → Bon de livraison → Facture → Avoir.
- **Cycle des achats** : Commande fournisseur → Bon de réception → Facture fournisseur → Avoir fournisseur.
- Transformation d'un document en un autre en un clic, numérotation automatique par année (`FA2026-00001`…).
- **Stock** : mouvements automatiques (BL, BR, factures non issues d'un BL/BR, avoirs), alertes, valorisation, et passage de la variation de stock en comptabilité (311 / 6031).
- **Règlements** : espèces, chèque, virement, Mobile Money ; imputation automatique sur les factures les plus anciennes.
- Impression des factures (format A4).

### Comptabilité OHADA (SYSCOHADA révisé)
- Plan comptable SYSCOHADA (classes 1 à 9) pré-chargé et modifiable.
- Journaux : Ventes (VT), Achats (AC), Banque (BQ), Caisse (CA), Mobile Money (MM), OD, À-nouveaux (AN).
- **Écritures automatiques** :
  | Opération | Écriture |
  |---|---|
  | Facture client | D 4111 TTC / C 70x HT / C 4431 TVA |
  | Facture fournisseur | D 60x HT / D 4452 TVA / C 4011 TTC |
  | Avoirs | Écriture inverse |
  | Encaissement client | D 52x / 57x / 55x / C 4111 |
  | Paiement fournisseur | D 4011 / C 52x / 57x / 55x |
  | Variation de stock | D 311 / C 6031 (ou inverse) |
- Saisie manuelle d'écritures (brouillard → validation, contrôle d'équilibre).
- Journaux, **grand livre**, **balance générale à 6 colonnes**, lettrage des comptes de tiers.
- **Bilan** (actif brut / amortissements / net, passif) et **Compte de résultat** avec les références officielles (TA…, RA…, XA à XI : marge commerciale, valeur ajoutée, EBE, résultat d'exploitation, financier, HAO, résultat net).
- Récapitulatif de la TVA (collectée / déductible / à reverser).
- Exercices comptables avec clôture (blocage des saisies).

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
python manage.py test
```

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
