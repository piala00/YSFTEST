# Laboratoire pédagogique : Société fictive SAHEL DISTRIBUTION (données entièrement inventées)

**Ne pas reprendre ces chiffres pour une entreprise réelle.** Utiliser une copie de formation Sage V12 disposant des droits d'exercice ; respecter les contraintes de l'édition et du paramétrage local.

## Organisation fictive

- Société : SAHEL DISTRIBUTION — S.A.R.L. fictive, située au Cameroun.
- Monnaie : FCFA ; règles fiscales = **à paramétrer selon la législation applicable** (ne pas présumer d'un taux fiscal).
- Dépôts : `DPT-PRINCIPAL` (magasin principal), `DPT-BOUTIQUE` (vente détail), `DPT-BOISSONS` (boissons uniquement), `DPT-TRANSIT` (transit logique ou physique selon paramétrage choisi).
- Familles : `BOISSONS`, `ALIMENTAIRE`, `SERVICES` (dernière sans stock si définie ainsi).
- Articles : `JUS-001` Jus mangue 1 L ; `EAU-001` Eau plate 1,5 L ; `RIZ-025` Riz sac 25 kg ; `TRANS-001` Frais de transport prestation (sans stock selon réglage).
- Clients : `CLI-GROS-01` (catégorie GROS, crédit), `CLI-DETAIL-01` (catégorie DETAIL, comptant), `CLI-ENC-01` (plafond de crédit fictif).
- Fournisseurs : `FOU-BOIS-01` (boissons), `FOU-ALIM-01` (aliments).
- Collaborateurs : `REP-A`, `REP-B` (commercial), `MAG-A` (magasinier), `ACC-A` (comptable) ; comptes réels à créer par administrateur si autorisé.

## Tarifs d'exercice (fictifs, avant taxes éventuelles)

| Référence | Achat fictif unitaire | Vente GROS fictive | Vente DÉTAIL fictive |
|---|---:|---:|---:|
| JUS-001 | 800 FCFA | 1 200 FCFA | 1 500 FCFA |
| EAU-001 | 250 FCFA | 350 FCFA | 450 FCFA |
| RIZ-025 | 13 000 FCFA | 15 500 FCFA | 16 000 FCFA |

Ces prix sont uniquement des données de laboratoire, pas des tarifs de marché. Les montants finaux dépendent des taxes, remises, devises et options du dossier.

## Stocks initiaux d'exercice

| Dépôt | JUS-001 | EAU-001 | RIZ-025 |
|---|---:|---:|---:|
| DPT-PRINCIPAL | 100 | 200 | 50 |
| DPT-BOUTIQUE | 20 | 40 | 10 |
| DPT-BOISSONS | 80 | 150 | 0 |

**Procédure** : créer article, dépôt et documents d'entrée ou inventaires de formation ; vérifier les stocks après mouvement. Ne pas saisir des chiffres dans SQL Server pour « initialiser ».

## Règles fictives de crédit

- `CLI-GROS-01` : crédit 30 jours, encours maximum théorique 300 000 FCFA.
- `CLI-DETAIL-01` : règlement au comptant.
- `CLI-ENC-01` : crédit 15 jours, encours maximum théorique 100 000 FCFA.

Pour les scénarios, la réaction à un dépassement dépend du code risque, des contrôles installés et du type de document. Enseigner cette dépendance.

## Preuves minimales à conserver

Pour chaque exercice, conserver : chemin du menu utilisé, captures anonymisées ou relevés des champs, n° de pièce de test, stock avant/après (si concerné), solde tiers avant/après, état de synthèse et observations sur la version/édition/permissions.
