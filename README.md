# ERP OHADA — Gestion commerciale · Comptabilité SYSCOHADA · Reporting

ERP conçu pour les PME de l'espace OHADA (FCFA, TVA 19,25 % par défaut — Cameroun). Il comprend :

- un **serveur web Django** (interface navigateur + API REST), compatible **PostgreSQL**, **SQL Server** ou SQLite ;
- un **client bureau CustomTkinter** (Windows / Linux / macOS) qui se connecte au serveur par l'API.

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

Ouvrir http://127.0.0.1:8000 et se connecter avec `admin` / `admin123`.

Sous Windows, double-cliquer sur `DEMARRER_SERVEUR.bat`.

## Base de données de production

Copier `.env.example` en `.env`, puis choisir le moteur :

- **PostgreSQL** : `DB_ENGINE=postgresql` (ou `docker compose up -d` pour un serveur prêt à l'emploi).
- **SQL Server** : `DB_ENGINE=mssql`, installer `mssql-django` (`pip install mssql-django`) et le pilote *ODBC Driver 18 for SQL Server*.

Ensuite : `python manage.py migrate && python manage.py init_erp --admin <mot_de_passe>`.

## Client bureau (CustomTkinter)

```bash
cd desktop
pip install -r requirements.txt
python app.py
```

Au premier lancement, saisir l'adresse du serveur (ex. `http://192.168.1.10:8000`), l'utilisateur et le mot de passe.
Le jeton est conservé dans `~/.erp_ohada.json`. Sous Windows : `desktop\DEMARRER_CLIENT.bat`, et `desktop\COMPILER.bat` pour produire `ERP_OHADA.exe`.

Fonctions disponibles : tableau de bord, ventes / achats (consultation, saisie et validation de factures, règlements), clients, fournisseurs, articles, balance, bilan, compte de résultat, balance âgée, exports CSV.

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

## Tests

```bash
python manage.py test
```

## Structure

```
erp/                 configuration Django (settings, urls)
apps/core/           société, exercices, numérotation, commande init_erp
apps/commercial/     tiers, articles, documents, règlements, stock
apps/comptabilite/   plan SYSCOHADA, journaux, écritures, états financiers
apps/reporting/      indicateurs et analyses
apps/api/            API REST (Django REST Framework)
templates/, static/  interface web (Bootstrap 5, Chart.js — servis localement, fonctionne hors ligne)
desktop/             client bureau CustomTkinter
```
