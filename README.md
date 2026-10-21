# ERP OHADA — Gestion commerciale · Comptabilité SYSCOHADA · Reporting

ERP conçu pour les PME de l'espace OHADA (FCFA, TVA 19,25 % par défaut — Cameroun). Il comprend :

- un **serveur web Django** (interface navigateur + API REST), compatible **PostgreSQL**, **SQL Server** ou SQLite ;
- un **client bureau CustomTkinter** (Windows / Linux / macOS) qui se connecte au serveur par l'API.

## Architecture : 3 logiciels, des onglets, des éléments et des sous-éléments

Chaque module est un **logiciel à part entière**, avec sa fenêtre, sa couleur et sa propre navigation :

```
Logiciel (module)          ex. Gestion commerciale
 └─ Onglets                 Structure · Ventes · Achats · Stock · Règlements · États
     └─ Éléments            Documents de vente · Nouveau document · Suivi
         └─ Sous-éléments   Devis · Bons de commande · Bons de livraison · Factures · Avoirs
```

| Logiciel | Onglets |
|---|---|
| **Gestion commerciale** | Structure, Ventes, Achats, Stock, Règlements, États |
| **Comptabilité OHADA** | Structure, Saisie, Traitement, États |
| **Reporting** | Synthèse, Ventes, Tiers, Finances |

Toute la navigation est décrite à un seul endroit : `apps/core/navigation.py`. Pour ajouter un onglet, un élément ou
un sous-élément, il suffit de l'y déclarer. Certains sous-éléments sont générés à partir des données, comme le plan
comptable par classe ou les écritures par journal. Cette même définition alimente :

- **le web** : le portail (`/`) ouvre chaque logiciel dans sa propre fenêtre du navigateur. Chaque logiciel affiche
  un en-tête à sa couleur, la barre d'onglets, l'arborescence des éléments à gauche et un fil d'Ariane ;
- **le client bureau** : il lit la structure via `/api/navigation/?module=<code>`.

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

Chaque logiciel est organisé ainsi : en-tête à sa couleur, barre d'onglets, arborescence des éléments et
sous-éléments, puis zone de travail. Les éléments qui disposent d'un écran natif s'affichent dans la fenêtre :
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
apps/core/           société, exercices, numérotation, navigation (modules/onglets/éléments), init_erp
apps/commercial/     tiers, articles, documents, règlements, stock
apps/comptabilite/   plan SYSCOHADA, journaux, écritures, états financiers
apps/reporting/      indicateurs et analyses
apps/api/            API REST (Django REST Framework)
templates/, static/  interface web (Bootstrap 5, Chart.js — servis localement, fonctionne hors ligne)
desktop/             logiciels bureau CustomTkinter (shell commun, écrans, lanceur)
```
